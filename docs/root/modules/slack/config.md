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
