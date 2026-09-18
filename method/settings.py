from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDT_Secret import GDT_Secret
from gdo.net.GDT_Url import GDT_Url


class settings(Method):
    """Per-Slack-server credentials and invitation URL.

    Configure these with the normal server config tool while in the target
    server context: ``$confs slack.settings <key> <value>``.
    """

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'slack.settings'

    def gdo_method_hidden(self) -> bool:
        return True

    def gdo_user_permission(self) -> str | None:
        return GDO_Permission.ADMIN

    @classmethod
    def gdo_method_config_server(cls) -> list[GDT]:
        return [
            GDT_Secret('slack_bot_token'),
            GDT_Secret('slack_app_token'),
            GDT_Secret('slack_signing_secret'),
            GDT_Url('slack_invite_url').all_schemes().in_and_external(),
        ]
