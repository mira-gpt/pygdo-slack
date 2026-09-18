from __future__ import annotations

from typing import Any

from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.web.async_client import AsyncWebClient

from gdo.base.Application import Application
from gdo.base.Logger import Logger
from gdo.base.Message import Message
from gdo.base.Render import Mode
from gdo.base.Util import Strings
from gdo.core.Connector import Connector
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDO_User import GDO_User
from gdo.core.GDO_UserPermission import GDO_UserPermission
from gdo.core.GDT_UserType import GDT_UserType


class Slack(Connector):
    """Bridge Slack Socket Mode events to and from a PyGDO server."""

    MAX_MSG_LEN = 39000

    def __init__(self):
        super().__init__()
        self._client: SocketModeClient | None = None
        self._web: AsyncWebClient | None = None
        self._dog: GDO_User | None = None
        self._bot_user_id: str | None = None

    def get_render_mode(self) -> Mode:
        return Mode.render_markdown

    def gdo_needs_authentication(self) -> bool:
        return False

    def render_user_connect_help(self) -> str:
        return 'Slack workspace'

    async def gdo_connect(self) -> bool:
        from gdo.slack.module_slack import module_slack

        module = module_slack.instance()
        if not module.cfg_bot_token() or not module.cfg_app_token():
            Logger.error('Slack is missing slack_bot_token or slack_app_token.')
            return False

        self._web = AsyncWebClient(token=module.cfg_bot_token())
        try:
            identity = await self._web.auth_test()
        except Exception as ex:
            Logger.exception(ex, 'Slack auth.test failed.')
            return False

        self._bot_user_id = str(identity['user_id'])
        self._dog = await self._server.get_or_create_user(self._bot_user_id, str(identity['user']))
        self._dog.save_val('user_type', GDT_UserType.CHAPPY)
        await GDO_UserPermission.grant(self._dog, GDO_Permission.ADMIN)
        await GDO_UserPermission.grant(self._dog, GDO_Permission.STAFF)

        self._client = SocketModeClient(app_token=module.cfg_app_token(), web_client=self._web)
        self._client.socket_mode_request_listeners.append(self.on_socket_request)
        try:
            await self._client.connect()
        except Exception as ex:
            Logger.exception(ex, 'Slack Socket Mode connect failed.')
            self._client = None
            return False
        self._connected = True
        await self.bootstrap_channels()
        Logger.info('Slack Socket Mode connected.')
        return True

    async def gdo_disconnect(self, quit_message: str):
        if self._client:
            await self._client.close()
        if self._web:
            await self._web.close()
        self._client = None
        self._web = None

    def gdo_get_dog_user(self) -> GDO_User | None:
        return self._dog

    async def on_socket_request(self, client: SocketModeClient, request: SocketModeRequest):
        """Acknowledge Socket Mode events, then pass normal messages to Dog."""
        """Acknowledge Slack promptly, then pass normal user messages to Dog."""
        if request.type != 'events_api':
            return
        await client.send_socket_mode_response(SocketModeResponse(envelope_id=request.envelope_id))
        payload = request.payload or {}
        event = payload.get('event') or {}
        if event.get('type') != 'message' or event.get('subtype'):
            return
        if event.get('bot_id') or str(event.get('user')) == self._bot_user_id:
            return
        text = (event.get('text') or '').strip()
        user_id = str(event.get('user') or '')
        channel_id = str(event.get('channel') or '')
        if not text or not user_id or not channel_id:
            return
        try:
            await self.handle_message(event, user_id, channel_id, text)
        except Exception as ex:
            Logger.exception(ex, 'Slack incoming message failed.')

    async def bootstrap_channels(self):
        """Register visible public channels so Dog can send before first inbound text."""
        if not self._web:
            return
        cursor = None
        while True:
            response = await self._web.conversations_list(
                types='public_channel',
                exclude_archived=True,
                limit=200,
                cursor=cursor,
            )
            for item in response.get('channels', []):
                channel_id = item.get('id')
                if channel_id:
                    # A visible public channel is not necessarily one the bot
                    # can post to. Join it once so outbound PyGDO relay is
                    # available before the first inbound Slack message.
                    if not item.get('is_member'):
                        try:
                            await self._web.conversations_join(channel=str(channel_id))
                        except Exception as ex:
                            Logger.error(f'Slack cannot join {channel_id}: {ex}')
                    self._server.get_or_create_channel(str(channel_id), item.get('name') or str(channel_id))
            cursor = response.get('response_metadata', {}).get('next_cursor') or None
            if not cursor:
                return

    async def handle_message(self, event: dict[str, Any], user_id: str, channel_id: str, text: str):
        Application.tick()
        user_name = user_id
        channel_name = channel_id
        # The relay deliberately needs no users:read scope. Slack's stable
        # member ID is sufficient for identity; known channels retain their
        # readable name from the connect-time channel bootstrap.
        if known_channel := self._server.get_channel_by_name(channel_id):
            channel_name = known_channel.gdo_val('chan_displayname') or channel_id
        user = await self._server.get_or_create_user(user_id, user_name)
        Application.set_current_user(user)
        channel = self._server.get_or_create_channel(channel_id, channel_name)
        await channel.on_user_joined(user)
        message = Message(text, Mode.render_markdown)
        message.env_server(self._server)
        message.env_user(user, True)
        message.env_channel(channel)
        await message.execute()

    async def gdo_send_to_channel(self, message: Message):
        channel = message._env_channel
        if not channel:
            return
        await self.send_to_conversation(channel.get_name(), message._result, message._env_reply_to)

    async def gdo_send_to_user(self, message: Message, notice: bool = False):
        await self.send_to_conversation(message._env_user.get_name(), message._result, message._env_reply_to)

    async def send_to_conversation(self, conversation_id: str, text: str, reply_to: GDO_User | None = None):
        if not self._web:
            raise RuntimeError('Slack is not connected.')
        prefix = '' if reply_to is None else f'{reply_to.get_displayname()}: '
        for chunk in Strings.split_boundary(text, self.MAX_MSG_LEN - len(prefix)):
            await self._web.chat_postMessage(channel=conversation_id, text=prefix + chunk, mrkdwn=True)
