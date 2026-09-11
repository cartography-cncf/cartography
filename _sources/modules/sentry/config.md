# Sentry Configuration

## Authentication

Create a Sentry [Internal Integration](https://docs.sentry.io/organization/integrations/integration-platform/internal-integration/):

1. Open **Settings** > **Developer Settings** > **Custom Integrations** > **Create New Integration**.
1. Select **Internal Integration**.
1. Save the integration and copy its generated token into an environment variable.

## Required Permissions

Grant the integration these scopes:

- `org:read`
- `member:read`
- `project:read`
- `project:releases`
- `alerts:read`
- `team:read`

## Configure Cartography

Provide these options:

- `--sentry-token-env-var`: Name of the environment variable containing the integration token.
- `--sentry-org`: Organization slug from a URL such as `https://sentry.io/organizations/<slug>/`.

## Run Cartography

```bash
export SENTRY_TOKEN='<integration-token>'
cartography \
  --selected-modules sentry \
  --sentry-token-env-var SENTRY_TOKEN \
  --sentry-org '<organization-slug>'
```

## Advanced Configuration

For a self-hosted instance, set `--sentry-host` to its host URL. The default is `https://sentry.io`.
