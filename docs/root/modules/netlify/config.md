## Netlify Configuration

Follow these steps to analyze Netlify objects with Cartography.

### 1. Create a personal access token

1. Go to [User settings > Applications > Personal access tokens](https://app.netlify.com/user/applications#personal-access-tokens)
   and create a new token.
1. A Netlify personal access token carries the full permissions of the user who created it, so
   create it from an account whose role in the team is as low as the sync allows. Cartography
   only issues `GET` requests, but the token itself is not read-only, so treat it as a
   privileged credential and store it accordingly.
1. Netlify invalidates every token created before a password reset, so a reset breaks the sync
   until the token is recreated.

### 2. Check the team member role

Cartography reads team-level and site-level resources, so the token's user needs to be a member
of the team you want to sync. Which resources come back depends on the role and on the team's
plan:

| Resource | Requirement |
|---|---|
| Team, members, sites, deploys, functions, forms, snippets, build hooks, notification hooks, deploy keys, DNS | Any team member role |
| Team-wide (shared) environment variables | A plan that includes shared environment variables. Cartography treats the 403 a Free team returns as "feature unavailable" and continues. |
| Dev servers, agent runners | A plan that includes them. Both are on the Free plan with a quota of one each. |
| Netlify DB branches and snapshots | Only fetched for sites whose payload reports `has_database`. |
| TLS certificates | Only present once a site has a custom domain with a provisioned certificate. |

### 3. Configure Cartography

1. Populate an environment variable with the token and pass its **name** with
   `--netlify-token-env-var`.
1. Pass the team slug with `--netlify-account-slug`. This is required: one run syncs one team.
   The slug is the segment in your team URL, `https://app.netlify.com/teams/<slug>/`, and
   `netlify api listAccountsForUser --data '{}'` lists every slug a token can see. Cartography
   fails with an explicit error listing the visible slugs if the one you pass is not among them.
1. Optionally override the API endpoint with `--netlify-base-url`
   (default: `https://api.netlify.com/api/v1`).

```bash
NETLIFY_TOKEN=your_token cartography \
  --selected-modules netlify \
  --netlify-token-env-var NETLIFY_TOKEN \
  --netlify-account-slug your-team-slug
```

### Secrets that are deliberately not ingested

Several Netlify endpoints return live credentials in plain text. Cartography drops them and
records only whether one is configured:

| Field | Handling |
|---|---|
| `envVar.values[].value` | Dropped. Netlify masks a secret value to its last four characters and returns a non-secret value in full; neither is stored. Only the key, scopes and deploy contexts are. |
| `databaseBranch.connection_string` | Dropped. Cartography never calls `GET /sites/{id}/database`, whose entire response body is the connection string, and uses the branches endpoint instead. |
| `buildHook.url` | Dropped. Anyone holding it can trigger a production deploy. |
| `hook.data` | Dropped. Holds the Slack incoming-webhook URL, target webhook URL or git provider token, depending on hook type. |
| `site.jwt_secret` | Dropped, replaced by `has_jwt_secret`. |
| `site.password` | Never returned by the API; `has_password` is ingested instead. |
| `deploy.skew_protection_token` | Dropped. |
| `serviceInstance.config`, `.env`, `.auth_url` | Dropped. Hold the credentials an add-on provisioned. |

### Rate limits

Netlify allows **500 requests per minute** and reports the remaining budget in
`X-RateLimit-Remaining`. A 429 comes with `Retry-After`, which the session's retry policy
honours, so no explicit throttling is needed. Cartography logs a warning when fewer than 25
requests remain in the current window.

The budget for a team with `S` sites is roughly:

| Call | Requests |
|---|---|
| List accounts (resolve the slug) | 1 |
| List members | 1 |
| List sites | ceil(S / 100) |
| Team-wide environment variables | 1 |
| Deploy keys | 1 |
| Per site: functions, dev servers, agent runners, environment variables, build hooks, notification hooks, snippets, service instances, TLS certificate, forms | 10 |
| Per site with a Netlify DB: branches, snapshots | 2 |
| DNS zones, plus one call per zone | 1 + Z |

That is about `10S + Z + 5` requests per sync, so the limit supports roughly 45 sites per
minute. Deploys cost nothing: the published deploy is embedded in the site payload.

Cartography always pages a list endpoint to the end. Handing a truncated result to the cleanup
jobs would make them delete every resource past the last page read, so a page that advertises a
successor it cannot reach raises `NetlifyPaginationError` instead of returning a short list.

### What is not ingested

- **Deploy history.** Only the deploy currently published on each site. The full history is an
  append-only list that can hold thousands of entries per site.
- **Agent runner sessions.** A session is a live execution record (prompt, step list, result
  diff) rather than inventory. The runner itself is ingested.
- **Form submissions.** The form is ingested with its field names and submission count; the
  submitted data is personal data and is left alone.
- **Audit log.** Retention is plan-gated and the volume is unbounded.
