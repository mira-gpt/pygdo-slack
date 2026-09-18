# pygdo-slack

Slack Socket Mode connector for the PyGDO8 framework. It creates one PyGDO
server, mirrors Slack users and conversations on first activity, and relays
ordinary messages in both directions.

## Local setup

Copy the included template and add Slack app credentials locally:

```bash
cp secret.example.toml secret.toml
```

`secret.toml` is ignored by Git. The initial connector needs a bot token, an
app-level Socket Mode token, and the signing secret from the Slack app.

## Slack app setup

Enable Socket Mode, install the app to the workspace, and grant the bot at
least `channels:history`, `channels:read`, `channels:join`, and `chat:write`.
Under Event Subscriptions, subscribe to the bot event `message.channels` (and
optionally `message.im` for direct messages). Then install the module with
PyGDO's normal module installer and restart Dog once so the connector is
loaded.
