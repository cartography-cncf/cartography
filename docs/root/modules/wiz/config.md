# Wiz Configuration

## Requirements

Create a Wiz service account for a custom GraphQL integration and grant it read access to the data you want Cartography to ingest.

The module needs:

- A Wiz GraphQL API endpoint, for example `https://api.us17.app.wiz.io/graphql`
- A Wiz OAuth token endpoint, usually `https://auth.app.wiz.io/oauth/token`
- A Wiz API client ID
- A Wiz API client secret

## CLI Options

| Option | Default | Required | Description |
|--------|---------|----------|-------------|
| `--wiz-graphql-url` |  | Yes | Wiz GraphQL API endpoint |
| `--wiz-auth-url` | `https://auth.app.wiz.io/oauth/token` | No | Wiz OAuth token endpoint |
| `--wiz-client-id-env-var` | `WIZ_CLIENT_ID` | Yes | Environment variable holding the Wiz API client ID |
| `--wiz-client-secret-env-var` | `WIZ_CLIENT_SECRET` | Yes | Environment variable holding the Wiz API client secret |
| `--wiz-tenant-id` | hostname of `--wiz-graphql-url` | No | Identifier used to scope all Wiz nodes in the graph |
| `--wiz-project-ids` |  | No | Comma-separated Wiz project IDs to import when project metadata is present |
| `--wiz-lookback-days` | `180` | No | Number of days of Wiz resource and finding updates to retrieve on each sync |

## Example

```bash
export WIZ_CLIENT_ID="..."
export WIZ_CLIENT_SECRET="..."

cartography \
  --selected-modules wiz \
  --wiz-graphql-url https://api.us17.app.wiz.io/graphql
```

`--wiz-project-ids` is applied to records that include Wiz project metadata. Records without project metadata are kept so vulnerability feeds that omit project data are not silently dropped.
