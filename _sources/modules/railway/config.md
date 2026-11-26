## Railway Configuration

Follow these steps to analyze Railway objects with Cartography.

1. Prepare your Railway API token.
    1. Create a token on your [account tokens page](https://railway.com/account/tokens).
       An **account** token can enumerate every workspace you belong to; a **workspace**
       token is limited to one workspace and cannot read the account-level API token
       inventory. Cartography handles both, and logs a warning for anything the token
       cannot reach.
       **Project tokens are not supported**: they authenticate with a
       `Project-Access-Token` header instead of `Authorization: Bearer` and can only see a
       single environment.
    1. Populate an environment variable with the token. Pass the environment variable name
       via CLI with `--railway-token-env-var`.
1. Optionally restrict the sync to one workspace with `--railway-workspace-id`. Without it,
   Cartography syncs every workspace the token can see. You can find the ID in the URL of
   your workspace settings page, or by running
   `railway api 'query { me { workspaces { id name } } }'`.
1. Optionally override the API endpoint with `--railway-base-url`
   (default: `https://backboard.railway.com/graphql/v2`).

### Rate limits

Railway's rate limit is applied **per hour**: 100 requests on the Free plan, 1000 on Hobby
and 10000 on Pro. Cartography keeps the request count low by pulling each project's
environments, service instances, domains, deployments, volumes and variables in a single
nested GraphQL document.

The budget for a workspace with `P` projects is roughly:

| Call | Requests |
|------|----------|
| Identify the account and its workspaces | 1 |
| Workspace details and members | 1 |
| List projects | ceil(P / 100) |
| Per-project bundle | P |
| Per-project TCP proxies (batched, 50 lookups per request) | P |
| Per-project tokens | P |
| Account API tokens | 1 |

That is about `3P + 3` requests per sync, so the Free plan supports roughly 30 projects per
hourly window. If a sync exhausts the quota, Cartography fails with an explicit error rather
than stalling for the remainder of the hour.

Each connection inside the bundle is capped at 100 items per request. A project with more
than 100 environments, services, service instances, volumes or variables costs one extra
request per additional page of the connection that overflowed. Cartography always pages to
the end for these: handing a truncated result to the cleanup jobs would make them delete
every resource past the first page.

Deployments are the exception. They are an append-only history that grows without bound, so
only the 10 most recent per environment are ingested and the connection is never paged. Older
revisions age out of the graph on the next sync instead of accumulating forever.
