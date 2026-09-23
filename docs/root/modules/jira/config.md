# Jira Configuration

Configure a Jira Cloud site and an API token owned by an account with permission
to read its users, groups, projects, and permission configuration.

## Prerequisites

Find the site's stable Cloud ID in the Atlassian administration URL, or use the
[documented Cloud ID lookup](https://support.atlassian.com/jira/kb/retrieve-my-atlassian-sites-cloud-id/).
Use this UUID for `--jira-cloud-id`; it scopes graph identifiers even after a
site rename. Jira Data Center and Server are not supported.

## Authentication

### Scoped API token

Create an [API token with scopes](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/)
for the importing account. Cartography sends Basic authentication using its
email address and token to
`https://api.atlassian.com/ex/jira/<cloud-id>/rest/api/3`.
Store the token in `JIRA_API_TOKEN` or another environment variable selected
with `--jira-api-token-env-var`.

### Unscoped API token

For an existing unscoped token, also provide
`--jira-site-url https://example.atlassian.net`. This uses the site's REST API
origin with the same email/token credentials. The site URL must correspond to
the configured Cloud ID. HTTPS Atlassian Cloud site origins are the only accepted
override destinations; redirects are rejected.

## Required Permissions

| Permission | Purpose |
|---|---|
| Browse users and groups | List all users and groups, including group membership. |
| Administer Jira | Enumerate all live projects and read every project's roles and scheme assignment. |

Both global permissions are checked before inventory begins. A less privileged
account could receive a successful but filtered project listing, so this module
requires these permissions instead of accepting that incomplete inventory. The
API token is only used for GET requests; no Jira configuration is changed.

For scoped tokens, enable the following union of granular read scopes documented
for the GET endpoints used by this module:

```text
read:application-role:jira
read:avatar:jira
read:field:jira
read:group:jira
read:issue-type-hierarchy:jira
read:issue-type:jira
read:permission-scheme:jira
read:permission:jira
read:project-category:jira
read:project-role:jira
read:project-version:jira
read:project.component:jira
read:project.property:jira
read:project:jira
read:user:jira
```

The project listing endpoint requires its documented project and issue-type
read scopes even though the module does not ingest issues. Token scopes do not
substitute for the account's Jira permissions. The endpoint references also
list the classic OAuth scopes `read:jira-user`, `read:jira-work`, and
`manage:jira-configuration` (group membership); OAuth authorization flows are
not implemented by this module.

## Configure Cartography

| Option | Required | Meaning |
|---|---|---|
| `--jira-cloud-id` | Yes | Stable Jira Cloud site UUID. |
| `--jira-email` | Yes | API-token owner's email address. |
| `--jira-api-token-env-var` | No | Token environment variable, default `JIRA_API_TOKEN`. |
| `--jira-site-url` | For unscoped tokens | HTTPS Atlassian site origin; otherwise the scoped-token gateway is used. |

## Run Cartography

```bash
export JIRA_API_TOKEN='your-api-token'
cartography --neo4j-uri bolt://localhost:7687 \
  --selected-modules jira \
  --jira-cloud-id 11111111-1111-4111-8111-111111111111 \
  --jira-email reader@example.com
```

## Troubleshooting

- **401/403**: Check token expiry, token scopes, email address, and the two
  required Jira global permissions. Scoped tokens use the gateway; unscoped
  tokens use the site URL override.
- **429 or transient failures**: The client retries GET requests up to three
  times on 429, 502, 503, and 504. Each `Retry-After` delay is capped at eight
  seconds; without that header, retries use exponential backoff.
  Exhausted retries abort the snapshot and preserve the previous graph. The
  connect/read timeouts are 10/60 seconds per request.
- **Missing emails**: Atlassian profile visibility may hide an email even from
  administrators. The account is still inventoried by account ID.
- **Admin or team-managed coverage**: See [access facts and coverage](index.md#access-facts-and-coverage).
  Bulk get groups, including its admin access filters, is experimental and may
  change; unsupported responses abort the sync rather than guessing access.

## References

- [Atlassian Jira Cloud REST v3 OpenAPI](https://dac-static.atlassian.com/cloud/jira/platform/swagger-v3.v3.json)
- [Users: Get all users](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-users/#api-rest-api-3-users-search-get)
- [Groups: Bulk get groups and Get users from group](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-groups/)
- [Projects: Get projects paginated](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-projects/#api-rest-api-3-project-search-get)
- [Project roles](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-project-roles/)
- [Project permission schemes](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-project-permission-schemes/)
- [Permission schemes and holder semantics](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-permission-schemes/)
- [Jira Cloud rate limiting](https://developer.atlassian.com/cloud/jira/platform/rate-limiting/)
