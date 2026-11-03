# LangSmith

```{toctree}
:hidden:
:maxdepth: 1

config
schema
```

Ingests the identity, access-control and agent-credential surface of
[LangSmith](https://docs.langchain.com/langsmith/) and LangGraph Platform.

The module exists to answer two questions the LangSmith UI cannot:

1. **Who can do what?** Organization and workspace members, the roles they hold in
   each workspace, what permission strings those roles actually grant, which
   attribute-based access policies narrow them, and every credential — personal
   access tokens, organization service keys, workspace API keys and SCIM tokens —
   that can act on their behalf.
2. **Which agents hold which user's OAuth tokens?** LangSmith lets a deployed agent
   act as a human against third-party APIs such as GitHub, Google, Slack or an
   arbitrary MCP server. This module inventories those grants, including their
   scopes and expiry.

## Tenancy model

LangSmith nests **organization → workspace → resources**. A workspace is called a
*tenant* in the API and in the `X-Tenant-Id` header.

Every organization-scoped node in this module hangs off `LangSmithOrganization` through
a `RESOURCE` relationship, so cleanup is scoped per organization. `LangSmithUser` is the
exception, described below. One sync run covers every
organization the configured token can see, or a single organization if
`--langsmith-org-id` is supplied.

Users are keyed on **`ls_user_id`**, the stable LangSmith user identifier. The API
also exposes a `user_id` (which mirrors the first linked auth provider's subject and
is not stable) and per-membership identity UUIDs. Neither is used as a node key.

Because the same person can belong to several organizations, `LangSmithUser` carries
only identity that is true of them everywhere — email, name, avatar. Everything
organization-specific (whether the identity is disabled, which organization role it
holds, how it was provisioned) lives on `LangSmithOrgMembership`. Writing that onto the
shared node would mean the last organization synced silently overwrote the others.

For the same reason `LangSmithUser` has no sub-resource relationship: it is not owned by
any single organization, and cleanup never deletes it. One organization's sync therefore
cannot destroy an identity another organization still references. This follows the same
pattern as `GitHubUser`, `ModalUser` and `RailwayUser`. Every relationship touching a
user is owned by an organization-scoped node or, for the `MEMBER_OF` shortcut to a
workspace, by an organization-scoped matchlink, so each organization only ever prunes its
own edges. Permission strings repeat across organizations too, so `LangSmithPermission`
is keyed `<organization_id>|<permission string>` and matched on `name`.

## Roles, permissions and memberships

A role assignment is a *(user, workspace, role)* triple, and LangSmith supports
organization-defined custom roles, so the role cannot be encoded as a fixed set of
relationship labels. Workspace role assignments are therefore modelled as their own
`LangSmithWorkspaceMembership` node:

```
(:LangSmithUser)-[:HAS_MEMBERSHIP]->(:LangSmithWorkspaceMembership)-[:IN_WORKSPACE]->(:LangSmithWorkspace)
(:LangSmithWorkspaceMembership)-[:HAS_ROLE]->(:LangSmithRole)-[:GRANTS]->(:LangSmithPermission)
```

`(:LangSmithUser)-[:MEMBER_OF]->(:LangSmithWorkspace)` is a shortcut for the same
membership, taken from the organization-level member listing so it survives a workspace
the token cannot read.

Organization roles work the same way, one membership per organization:

```
(:LangSmithUser)-[:HAS_MEMBERSHIP]->(:LangSmithOrgMembership)-[:HAS_ROLE]->(:LangSmithRole)
```

```{note}
LangSmith stores **every** organization-defined custom role under the system name
`CUSTOM`. Match on `LangSmithRole.name` (the display name) or `id`, never on
`system_name`.
```

## Agent credentials

A LangSmith agent can hold an OAuth token for a third-party provider, scoped to the
human who authorized it, and then call that provider's API as them. Those grants are
this module's central subject:

```
(:LangSmithAgent)-[:HAS_CREDENTIAL]->(:LangSmithAgentCredential)-[:FOR_PROVIDER]->(:LangSmithOAuthProvider)
(:LangSmithAgentCredential)-[:ON_BEHALF_OF]->(:LangSmithUser)
```

The credential carries the granted `scopes` and `expires_at`. `oauth_token_id` is an
opaque reference to the stored token; no token material is requested or returned.

Agents are discovered by listing each deployment's assistants, because a LangSmith agent
id is an *assistant* id and the control plane does not expose it: a deployment carries an
`agent` block only when it was created with an explicit agent binding, and for most
deployments that is `null`.

That listing requires `X-Tenant-Id` and costs one request per deployment, against the
deployment's own data plane. Two things keep the cost bounded:

* **Only `READY` deployments are probed.** The other states (`AWAITING_DATABASE`,
  `UNUSED`, `AWAITING_DELETE`, `AWAITING_FINAL_DELETE`, `UNKNOWN`) cannot serve, and
  asking one costs a full timeout to learn nothing. Non-serving deployments are still
  ingested as nodes; they are simply not probed.
* **The probes run concurrently**, since each targets an independent host. A
  scaled-to-zero deployment waking slowly no longer holds up the rest.

A failure (a timeout, or a credential the deployment rejects) marks discovery
incomplete without breaking the sync. Assistants already retrieved are kept, and agent
cleanup is skipped rather than reading the result as an empty inventory.

Because an assistant id is derived from its graph, one agent is commonly served by
several deployments, so `RUNS` is a one-to-many edge. For the same reason agent nodes are
keyed `<organization_id>|<assistant_id>`: two organizations running the same graph would
otherwise share an agent node, merging their deployments and credential paths. The raw
assistant id is kept as a property, because the agent-auth API is keyed by it.

Credentials resolve their provider to that provider's UUID during transform rather than
matching on the `provider_id` slug. The slug is operator-chosen, so two organizations can
both define one called `github-prod`, and relationship matching carries no implicit
organization constraint.

## What this module deliberately does not ingest

```{note}
This module talks to a credential-bearing API and is deliberately conservative about
what it stores.
```

* **Secret and token values.** Workspace secrets are ingested as key **names** only.
  Deployment environment secrets arrive as `{name, value}` pairs and the values are
  dropped during transform, before the records reach the graph. Only the non-secret
  `short_key` prefix of a credential is stored.
* **Caller-scoped endpoints.** LangSmith filters its own token and authorized-app
  listings to the calling user, so they would only ever return the collector token
  owner's own rows and would produce a misleadingly sparse graph. The organization-wide
  view comes from the per-agent connection route instead.
* **Audit logs.** Time-series data rather than graph-shaped; out of scope.
* **Resource taggings.** The tag vocabulary is ingested as `LangSmithResourceTag`, but
  the edges attaching tags to individual projects, datasets and prompts are not, because
  those resource types are outside this module's scope.
* **SCIM group membership.** `/scim/v2/Groups` requires a SCIM token rather than a
  personal access token, so group membership is not reachable. The SCIM *token*
  inventory is collected.

## Graceful degradation, and why it does not delete anything

A token commonly holds `workspaces:read` or `deployments:read` in only some workspaces,
and listing every member's personal access tokens additionally requires
`organization:pats:read`. Each workspace-scoped fetch and each optional listing degrades
to a logged warning rather than failing the module.

Crucially, a degraded fetch is tracked as an **incomplete collection**, not as an empty
one. Cleanup deletes nodes whose `lastupdated` does not match the current run, so a
failed listing that silently returned nothing would look exactly like "these no longer
exist" and delete live agents along with their credentials. When a fetch fails with a
401 or 403, a timeout, or a deployment that will not answer, cleanup for that node type
is skipped and a warning is logged. Other node types still clean up. Stale nodes are the
lesser harm.

A 404 is different: LangSmith answers it for features an organization does not have,
such as SCIM tokens, access policies or hybrid data planes, and for an agent that agent
auth has never seen. Every optional listing treats a 404 as a complete, empty answer, so
cleanup proceeds. A 404 on a workspace-scoped route for a workspace that was just listed
means the workspace itself is gone, so its resources are cleaned up too.

The organization info, workspace list and organization member list are required. If one
of those cannot be read, the sync for that organization fails rather than producing a
graph with no anchor.

`LangSmithOrganization` nodes are never cleaned up. A run restricted with
`--langsmith-org-id` sees only one organization, so absence from a run is not evidence
of deletion.

```{note}
Credentials are never sent to a deployment over plaintext HTTP, and redirects from a
deployment are refused rather than followed. Deployment hosts come from API data rather
than operator configuration, and `requests` strips only the `Authorization` header when a
redirect changes host — a custom `X-Api-Key` would be forwarded intact.
```

## Example queries

Which agents can act as which humans, against what, with which scopes:

```cypher
MATCH (a:LangSmithAgent)-[:HAS_CREDENTIAL]->(c:LangSmithAgentCredential)
      -[:FOR_PROVIDER]->(p:LangSmithOAuthProvider)
MATCH (c)-[:ON_BEHALF_OF]->(u:LangSmithUser)
RETURN u.email, a.id, p.name, c.scopes, c.expires_at
```

Deactivated members who still hold live tokens, and agents still acting as them:

```cypher
MATCH (u:LangSmithUser)-[:HAS_MEMBERSHIP]->(:LangSmithOrgMembership {is_disabled: true})
OPTIONAL MATCH (u)<-[:OWNED_BY]-(k:LangSmithApiKey) WHERE k.revoked_at IS NULL
OPTIONAL MATCH (u)<-[:ON_BEHALF_OF]-(c:LangSmithAgentCredential)
RETURN u.email, collect(DISTINCT k.short_key), collect(DISTINCT c.id)
```

Everyone who can administer the organization, including through custom roles:

```cypher
MATCH (u:LangSmithUser)-[:HAS_MEMBERSHIP]->(:LangSmithOrgMembership)
      -[:HAS_ROLE]->(r:LangSmithRole)
      -[:GRANTS]->(:LangSmithPermission {name: 'organization:manage'})
RETURN u.email, r.name
```

Who can read raw agent credentials, since `deployments:read` alone is sufficient:

```cypher
MATCH (u:LangSmithUser)-[:HAS_MEMBERSHIP]->(m:LangSmithWorkspaceMembership)
      -[:HAS_ROLE]->(r:LangSmithRole)-[:GRANTS]->(:LangSmithPermission {name: 'deployments:read'})
MATCH (m)-[:IN_WORKSPACE]->(w:LangSmithWorkspace)
RETURN w.name, r.name, collect(u.email)
```

Deployments shareable outside the organization:

```cypher
MATCH (w:LangSmithWorkspace)-[:CONTAINS]->(d:LangSmithDeployment {shareable: true})
RETURN w.name, d.name, d.url
```

## Ontology

The module maps into the shared ontology through `UserAccount`, `Tenant`,
`PermissionRole`, `ServiceAccount`, `APIKey`, `IdentityProvider`, `ThirdPartyApp`,
`Secret` and `Tag` labels, so LangSmith identities join cross-provider queries
against the canonical `User` node.
