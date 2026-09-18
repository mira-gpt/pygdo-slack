# pygdo-slack

Slack connector for the PyGDO8 framework.

The connector will bridge Slack channels and PyGDO Dog events through Slack's
Socket Mode and Events API. It intentionally keeps local credentials out of
the repository.

## Local setup

Copy the included template and add Slack app credentials locally:

```bash
cp secret.example.toml secret.toml
```

`secret.toml` is ignored by Git. The initial connector needs a bot token, an
app-level Socket Mode token, and the signing secret from the Slack app.
