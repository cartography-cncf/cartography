# Infisical Configuration

Configure an Infisical Machine Identity with Universal Auth and read access to
the projects in the organization you want to ingest.

## Prerequisites

Create a Machine Identity in the target Infisical organization and configure
Universal Auth for it.

## Authentication

### Universal Auth

Cartography exchanges the Machine Identity client ID and client secret for a
short-lived access token. Store both credentials in environment variables.

## Required Permissions

The Machine Identity must be able to list projects in the configured
organization through `GET /api/v2/organizations/{organizationId}/workspaces`.

Cartography does not request secret values.

## Configure Cartography

| Option | Default | Required | Description |
|--------|---------|----------|-------------|
| `--infisical-api-url` | `https://app.infisical.com` | No | Infisical API origin. Change this for self-hosted Infisical. |
| `--infisical-organization-id` |  | Yes | Organization identifier whose projects will be ingested. |
| `--infisical-client-id-env-var` | `INFISICAL_CLIENT_ID` | No | Environment variable containing the Machine Identity client ID. |
| `--infisical-client-secret-env-var` | `INFISICAL_CLIENT_SECRET` | No | Environment variable containing the Machine Identity client secret. |

## Run Cartography

```bash
export INFISICAL_CLIENT_ID="..."
export INFISICAL_CLIENT_SECRET="..."

cartography \
  --selected-modules infisical \
  --infisical-organization-id "your-organization-id"
```

## References

- [Infisical Universal Auth](https://infisical.com/docs/documentation/platform/identities/universal-auth)
- [Infisical API reference](https://infisical.com/docs/api-reference/overview/introduction)
