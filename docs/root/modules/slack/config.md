## Slack Configuration

.. _slack_config:

Follow these steps to analyze Slack objects with Cartography.

1. Create a Slack integration
    1. Go to `https://api.slack.com/apps/` and create a new integration
    1. Add bot permissions in `OAuth & Permissions`
        - channels:read
        - groups:read
        - team.preferences:read
        - team:read
        - usergroups:read
        - users.profile:read
        - users:read
        - users:read.email
    1. Install the App on your Slack Workspace
    1. Get "Bot User OAuth Token" and store it into an env var
    1. Provide env var name with `--slack-token-env-var ENV_VAR_NAME` parameter

```{note}
By default, Cartography will ingest data from the Slack workspaces associated with the provided token. You can optionally specify particular Slack Team IDs to limit the ingestion scope.
```

2. Get your Slack Team ID (Optional)
    1. In a web-browser go to `https://<your-team>.slack.com`
    1. You will be redirected to `https://app.slack.com/client/<your-team-id>`
    1. Use `--slack-teams <your-team-id>` parameter (you can provide multiple teams id comma separated)
