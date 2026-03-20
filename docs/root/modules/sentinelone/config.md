## SentinelOne Configuration

Follow these steps to analyze SentinelOne objects with Cartography.

1. Prepare a SentinelOne API token with appropriate permissions.
1. Pass the SentinelOne API URL to the `--sentinelone-api-url` CLI arg.
1. Populate an environment variable with the API token.
1. Pass that environment variable name to the `--sentinelone-api-token-env-var` CLI arg.
1. Optionally, pass specific account IDs to sync using the `--sentinelone-account-ids` CLI arg (comma-separated).
1. Optionally, pass specific site IDs to sync using the `--sentinelone-site-ids` CLI arg (comma-separated).

## Required Permissions

The API token requires the following permissions:
- **Account** - Read access to account information
- **Agent** - Read access to agent information

## MSSP And Site-Scoped Deployments

Some SentinelOne MSSP deployments issue API tokens for site-scoped users. Those
tokens can query site, agent, application inventory, and risk endpoints but
cannot call `/web/api/v2.1/accounts`. When Cartography receives SentinelOne's
`4030010` "Action is not allowed to site users" response from the accounts
endpoint, it automatically falls back to enumerating `/web/api/v2.1/sites`.

In that fallback mode:

- Cartography synthesizes `S1Account` nodes from the parent account metadata on
  each site response so the existing graph model remains intact.
- Resources are fetched per site and attached to their parent `S1Account`.
- `--sentinelone-site-ids` can be used to limit the sync to specific sites.

If you know you are using an MSSP or site-scoped token, prefer
`--sentinelone-site-ids` over `--sentinelone-account-ids`.
