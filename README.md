# pygdo-slack

Slack Socket Mode connector for the PyGDO8 framework. It creates one PyGDO
server, mirrors Slack users and conversations on first activity, and relays
ordinary messages in both directions.

## Prerequisites

- A running PyGDO8/Dog installation.
- A Slack workspace in which you may create and install an app.
- Python dependencies from [`requirements.txt`](requirements.txt), installed
  into the interpreter used by Dog.

## Create and configure the Slack app

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and create an app
   **from scratch** for the target workspace.
2. Under **Socket Mode**, enable Socket Mode and create an app-level token
   with the `connections:write` scope. It begins with `xapp-`.
3. Under **OAuth & Permissions**, add these bot-token scopes:

   - `channels:history`
   - `channels:join`
   - `channels:read`
   - `chat:write`
   - `users:read`

   `users:read` lets the connector resolve names for its in-memory user list.
4. Under **Event Subscriptions**, enable events and subscribe to these
   **bot events**:

   - `message.channels`
   - `member_joined_channel`
   - `member_left_channel`

5. Under **Basic Information**, copy the signing secret. Under **OAuth &
   Permissions**, install or reinstall the app to the workspace and copy the
   bot token (`xoxb-`). Reinstalling is required after scope or event changes.

## Initial local secret file

Copy the included template and fill in the values locally:

```bash
cp secret.example.toml secret.toml
```

`secret.toml` is ignored by Git and must never be committed. It contains the
initial bot token, app-level Socket Mode token, signing secret, and optional
workspace invitation URL:

```toml
[slack]
bot_token = "xoxb-..."
app_token = "xapp-..."
signing_secret = "..."
invite_url = "https://join.slack.com/t/<workspace>/shared_invite/..."
```

## Install and start

Install the module through PyGDO's normal module installer, then restart Dog.
On connection, the bot discovers public channels and joins those it can join.
Each Slack channel becomes a PyGDO channel after its first activity.

## Per-server settings

The file is a convenient bootstrap and recovery mechanism. Once Dog is
running, credentials and the invitation link can be overridden per Slack
server using the regular server-configuration command from that server's
channel context:

```text
$confs slack.settings slack_invite_url https://join.slack.com/t/<workspace>/shared_invite/...
$confs slack.settings slack_bot_token xoxb-...
$confs slack.settings slack_app_token xapp-...
```

The per-server value wins over `secret.toml`; use `NULL` to remove an override
and fall back to the local secret file. Secrets are redacted by the normal
PyGDO configuration renderer. The invitation link is shown as a clickable link
on PyGDO's Connect page.

For a second workspace, add a second PyGDO server using the Slack connector,
enter the desired Slack server context, configure its own `slack.settings`
values, and restart Dog. This keeps credentials and invite links separated by
server.

## Troubleshooting

- `missing_scope` from `users.info`: add `users:read`, then reinstall the Slack
  app.
- Socket Mode connects but no messages arrive: check that
  `message.channels` is enabled and the app was reinstalled afterwards.
- Missing join/leave updates: subscribe to `member_joined_channel` and
  `member_left_channel`, then reinstall.
- A changed token or server setting takes effect after a Dog restart.
