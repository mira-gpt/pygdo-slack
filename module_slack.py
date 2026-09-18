from __future__ import annotations

import tomlkit

from gdo.base.GDO_Module import GDO_Module
from gdo.base.GDT import GDT
from gdo.core.Connector import Connector
from gdo.core.GDO_Server import GDO_Server
from gdo.core.GDT_Secret import GDT_Secret
from gdo.core.GDT_String import GDT_String

from .connector.Slack import Slack


class module_slack(GDO_Module):
    """Slack Socket Mode connector configuration and registration."""

    def gdo_module_config(self) -> list[GDT]:
        values = {'bot_token': '', 'app_token': '', 'signing_secret': ''}
        try:
            with open(self.file_path('secret.toml'), 'r', encoding='utf-8') as file:
                values.update(tomlkit.load(file).get('slack', {}))
        except FileNotFoundError:
            pass
        return [
            GDT_Secret('slack_bot_token').initial(str(values['bot_token'])),
            GDT_Secret('slack_app_token').initial(str(values['app_token'])),
            GDT_Secret('slack_signing_secret').initial(str(values['signing_secret'])),
            GDT_String('slack_display_name').initial('Slack'),
        ]

    def cfg_bot_token(self) -> str:
        return self.get_config_val('slack_bot_token')

    def cfg_app_token(self) -> str:
        return self.get_config_val('slack_app_token')

    def cfg_signing_secret(self) -> str:
        return self.get_config_val('slack_signing_secret')

    def cfg_display_name(self) -> str:
        return self.get_config_val('slack_display_name')

    def gdo_init(self):
        Connector.register(Slack)

    async def gdo_install(self):
        if not GDO_Server.get_by_connector('slack'):
            GDO_Server.blank({
                'serv_name': 'Slack',
                'serv_username': self.cfg_display_name(),
                'serv_connector': 'slack',
                'serv_trigger': '.',
            }).insert()
