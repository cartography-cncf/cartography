## SentinelOne Configuration

Follow these steps to analyze SentinelOne objects with Cartography.

### Create a Service User in SentinelOne

1. In SentinelOne, open **Settings**.
1. From the top menu, select **Users**.
1. In the left-hand menu, select **Service Users**.
1. Select **Actions** and then **Create New Service User**.
1. Enter a name and expiration date for the Service User and select **Next**.
1. Choose the account or site that the Service User should have access to and select **Create**.
1. Copy the API token when it is shown. SentinelOne only displays it once.

The default **Viewer** role is sufficient for Cartography.

### Configure Cartography

1. Pass the SentinelOne API URL to the `--sentinelone-api-url` CLI arg.
1. Populate an environment variable with the API token.
1. Pass that environment variable name to the `--sentinelone-api-token-env-var` CLI arg.
1. Optionally, pass specific account IDs to sync using the `--sentinelone-account-ids` CLI arg (comma-separated).
1. Optionally, pass specific site IDs to sync using the `--sentinelone-site-ids` CLI arg (comma-separated).

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
- When `--sentinelone-site-ids` is used, Cartography skips account-wide cleanup
  so data from sibling sites under the same account is not deleted.

If you know you are using a site-scoped token, prefer
`--sentinelone-site-ids` over `--sentinelone-account-ids`. If you do not pass
explicit site IDs, Cartography will sync all sites visible to that token.
