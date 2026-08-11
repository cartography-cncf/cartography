# Wiz Configuration

Configure a Wiz service account that can read entities through the Wiz GraphQL
API, then provide Cartography with the API endpoint and service account
credentials.

## Authentication

Create a Wiz service account for a custom integration:

1. In Wiz, open **Settings**.
1. Select **Tenant**.
1. Select **General**.
1. Select **Access Management**.
1. Select **Add Service Account**.
1. Choose **Custom Integration**.
1. Leave the project selection empty.
1. Under scopes, select **Read all entities**.
1. Copy the client ID and client secret. Wiz only displays the secret when the
   service account is created.

Open `https://app.wiz.io/tenant-info/general` and copy the API endpoint URL.
It should look similar to `https://api.us17.app.wiz.io/graphql`.

## Required Permissions

| Permission | Purpose |
|------------|---------|
| `Read all entities` | Allows Cartography to read Wiz issues, vulnerability findings, detection findings, and failing configuration findings. |

## Configure Cartography

Store the Wiz service account credentials in environment variables. By default,
Cartography reads `WIZ_CLIENT_ID` and `WIZ_CLIENT_SECRET`; use
`--wiz-client-id-env-var` and `--wiz-client-secret-env-var` if you choose
different names.

| Option | Default | Required | Description |
|--------|---------|----------|-------------|
| `--wiz-graphql-url` |  | Yes | Wiz GraphQL API endpoint. |
| `--wiz-auth-url` | `https://auth.app.wiz.io/oauth/token` | No | Wiz OAuth token endpoint. |
| `--wiz-client-id-env-var` | `WIZ_CLIENT_ID` | Yes | Environment variable holding the Wiz API client ID. |
| `--wiz-client-secret-env-var` | `WIZ_CLIENT_SECRET` | Yes | Environment variable holding the Wiz API client secret. |
| `--wiz-tenant-id` | Hostname of `--wiz-graphql-url` | No | Identifier used to scope all Wiz nodes in the graph. |
| `--wiz-project-ids` |  | No | Comma-separated Wiz project IDs to import when project metadata is present. Cleanup is skipped in this mode. |
| `--wiz-lookback-days` |  | No | Fetch only Wiz issue and finding updates from the last N days. Cleanup is skipped in this mode. |

## Run Cartography

```bash
export WIZ_CLIENT_ID="..."
export WIZ_CLIENT_SECRET="..."

cartography \
  --selected-modules wiz \
  --wiz-graphql-url https://api.us17.app.wiz.io/graphql
```

## Advanced Configuration

By default, Cartography performs a complete Wiz sync and runs cleanup for stale
Wiz issues and findings. Set `--wiz-lookback-days` only for incremental imports
where preserving older unchanged records is preferable to deleting stale
records.

Configuration findings are limited to failing checks. A complete sync imports
active failing checks; lookback mode also fetches recently updated resolved or
rejected failures so their status can be refreshed without cleanup.

`--wiz-project-ids` is applied to records that include Wiz project metadata.
Records without project metadata are kept so finding feeds that omit project
data are not silently dropped. Project-filtered imports are partial tenant
syncs, so cleanup is skipped. Run an unfiltered complete sync when stale record
cleanup is required.
