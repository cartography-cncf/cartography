# Jira

The Jira Cloud module inventories accounts, groups and memberships, live projects,
project roles and their actors, and company-managed project permission grants.
It does not ingest issues or create tickets.

`JiraUser` accounts of type `atlassian` carry the `UserAccount` ontology label.
Visible email addresses can link these accounts to canonical users with
`--selected-modules jira,ontology --ontology-users-source jira`. Hidden email
addresses are left absent; the module does not infer them from names.
The complete user listing supplies profile fields; nested membership and lead
profiles supply fields only for accounts absent from that listing.
`JiraTenant` carries the `Tenant` ontology label.
Atlassian's inactive, corrupted deleted-user records with account ID `unknown`
are omitted. References to these tombstones remain unlinked; their permission
grant facts are retained. Missing identifiers or unavailable user profiles
still abort the snapshot.

## Access facts and coverage

- Users and groups connect to project roles through `MEMBER_OF`. Roles, groups,
  and direct user holders connect to `JiraPermissionGrant` through
  `HAS_PERMISSION`; grants connect to their project through `APPLIES_TO`.
- Grants retain the permission key and original holder type, parameter, and
  value. Conditional holders such as reporter, assignee, application roles,
  custom fields, and anyone remain configuration facts. Role membership alone
  is not treated as effective project or issue access. Product licensing,
  account suspension, issue security, and service-project portal rules can
  further restrict access.
- Team-managed projects have project role/actor data and
  `permission_scheme_supported=false`. Their permission schemes and project
  access-level policy are not exported. Archived/deleted projects are outside
  this module's live-project inventory.
- `JiraGroup.admin_access_types` contains the `admin` and/or `site-admin` values
  returned by Atlassian's **experimental** Bulk get groups endpoint. These
  groups have `ADMIN_OF` edges to the site. This reports group-designated admin
  access; it is not a complete inventory of arbitrary global permission grants,
  organization admins, or an effective per-user administrator check. Group
  names are never used to guess administrative privilege.

The module validates the entire API snapshot before loading it. Any failed or
malformed response aborts the sync before graph writes and cleanup. A successful
sync removes stale records only within the configured Jira Cloud ID. Membership
reads include inactive users. Atlassian APIs do not provide a transactional
snapshot, so concurrent administrative changes may require a rerun.

## Sync cost

Requests scale with pages of users (up to 1,000 per page), groups and memberships
(50 per page), and projects (50 per page), plus two paginated admin-group queries.
Each project needs one role-list request and one request per role. Each
company-managed project needs one permission-scheme assignment request; each
unique scheme is fetched once. There are also two preflight/site-info requests.
No per-user by per-project permission checks are performed.
Requests reuse one session and run sequentially to limit concurrent API load.
The module logs group and project counts before fetching their detail records.
Each paginated listing is limited to 10,000 pages. If Jira keeps returning pages
past that limit, the sync fails before graph writes or cleanup.

```{toctree}
config
schema
queries
```
