# Slack Configuration

## Authentication

1. Create an app at [Slack API Apps](https://api.slack.com/apps/).
1. Add the required bot scopes under **OAuth & Permissions**.
1. Install the app in the Slack workspace.
1. Copy the **Bot User OAuth Token** into an environment variable.

## Required Permissions

Add these bot scopes:

- `channels:read`
- `groups:read`
- `team.preferences:read`
- `team:read`
- `usergroups:read`
- `users.profile:read`
- `users:read`
- `users:read.email`

```{note}
`channels:read` covers public channels and `groups:read` covers private ones. A bot
token can only see private channels the bot is **a member of** — no scope grants a
bot workspace-wide private channel visibility, so private channel coverage is
limited to the channels the bot was invited to. Enumerating every private channel
in a workspace requires an Enterprise Grid **user** token with
`admin.conversations:read`, which Cartography does not currently support.
```

## Configure Cartography

Use `--slack-token-env-var` to provide the name of the environment variable containing the bot token.

## Run Cartography

```bash
export SLACK_BOT_TOKEN='<bot-user-oauth-token>'
cartography \
  --selected-modules slack \
  --slack-token-env-var SLACK_BOT_TOKEN
```

## Advanced Configuration

By default, Cartography ingests every Slack workspace associated with the token. To limit ingestion, use `--slack-teams` with a comma-separated list of team IDs.

To find a team ID, open `https://<your-team>.slack.com` in a browser. Slack redirects to a URL in the form `https://app.slack.com/client/<your-team-id>`.

To ingest channel membership, use `--slack-channels-memberships`. This makes one
`conversations.members` call per channel at Slack's tier-2 rate limits, so it may be
slow for large workspaces. Private channels the bot belongs to count toward that
total alongside public ones.
