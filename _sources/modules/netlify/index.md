# Netlify

The Netlify module ingests a Netlify team and everything it owns: sites and their published
deploy, functions, dev servers, agent runners, Netlify DB branches and snapshots, environment
variables, build and notification hooks, deploy keys, snippets, add-on service instances, DNS
zones and records, TLS certificates and forms. See [configuration](config.md) for token and team
setup, and the generated [schema](schema.md) for every node, property and relationship.

```{toctree}
config
schema
```

## Tenancy

Netlify has a single tenancy level. A team (`NetlifyAccount`) owns everything, and every node in
this module is scoped to that team for cleanup, including the ones that also hang off a site. One
Cartography run syncs one team, so `--netlify-account-slug` is required.

Users are the exception to that ownership. A Netlify user is a shared identity that can belong to
several teams, so the node is never deleted by a team's cleanup and both of its team edges are
scoped to the team being synced. Ask who is on a team by traversing `MEMBER_OF`, not by node
existence. An address invited to a team that has not accepted yet has no Netlify user behind it,
so it becomes a `NetlifyInvite` keyed on the email instead.

## Secrets that are deliberately not ingested

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

## What is not ingested

- **Deploy history.** Only the deploy currently published on each site. The full history is an
  append-only list that can hold thousands of entries per site.
- **Agent runner sessions.** A session is a live execution record (prompt, step list, result
  diff) rather than inventory. The runner itself is ingested.
- **Form submissions.** The form is ingested with its field names and submission count; the
  submitted data is personal data and is left alone.
- **Audit log.** Retention is plan-gated and the volume is unbounded.

## Rate limits

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
