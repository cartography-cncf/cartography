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

Every node in this module hangs off `LangSmithOrganization` through a `RESOURCE`
relationship, so cleanup is scoped per organization. One sync run covers every
organization the configured token can see, or a single organization if
`--langsmith-org-id` is supplied.

Users are keyed on **`ls_user_id`**, the stable LangSmith user identifier. The API
also exposes a `user_id` (which mirrors the first linked auth provider's subject and
is not stable) and per-membership identity UUIDs. Neither is used as a node key; the
organization-scoped identity UUID is retained as `org_identity_id`.

## Roles, permissions and memberships

A role assignment is a *(user, workspace, role)* triple, and LangSmith supports
organization-defined custom roles, so the role cannot be encoded as a fixed set of
relationship labels. Workspace role assignments are therefore modelled as their own
`LangSmithWorkspaceMembership` node:

```
(:LangSmithUser)-[:HAS_MEMBERSHIP]->(:LangSmithWorkspaceMembership)-[:IN_WORKSPACE]->(:LangSmithWorkspace)
(:LangSmithWorkspaceMembership)-[:HAS_ROLE]->(:LangSmithRole)-[:GRANTS]->(:LangSmithPermission)
```

Organization-level roles are simpler — one per user — and attach directly:
`(:LangSmithUser)-[:HAS_ROLE]->(:LangSmithRole)`.

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
deployments that is `null`. Listing assistants requires `X-Tenant-Id` and costs one
request per deployment with a serving URL. Deployments can be scaled to zero and take
longer than a normal request to wake, so failures degrade to an empty assistant list
rather than breaking the sync.

Because an assistant id is derived from its graph, one agent is commonly served by
several deployments, so `RUNS` is a one-to-many edge.

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

## Graceful degradation

A token commonly holds `workspaces:read` or `deployments:read` in only some
workspaces, and listing every member's personal access tokens additionally requires
`organization:pats:read`. Each workspace-scoped fetch and each optional credential
listing degrades to a logged warning and an absent subgraph rather than failing the
module.

## Example queries

Which agents can act as which humans, against what, with which scopes:

```cypher
MATCH (a:LangSmithAgent)-[:HAS_CREDENTIAL]->(c:LangSmithAgentCredential)
      -[:FOR_PROVIDER]->(p:LangSmithOAuthProvider)
MATCH (c)-[:ON_BEHALF_OF]->(u:LangSmithUser)
RETURN u.email, a.id, p.name, c.scopes, c.expires_at
```

Deactivated users who still hold live tokens, and agents still acting as them:

```cypher
MATCH (u:LangSmithUser {is_disabled: true})
OPTIONAL MATCH (u)<-[:OWNED_BY]-(k:LangSmithApiKey) WHERE k.revoked_at IS NULL
OPTIONAL MATCH (u)<-[:ON_BEHALF_OF]-(c:LangSmithAgentCredential)
RETURN u.email, collect(DISTINCT k.short_key), collect(DISTINCT c.id)
```

Everyone who can administer the organization, including through custom roles:

```cypher
MATCH (u:LangSmithUser)-[:HAS_ROLE]->(r:LangSmithRole)
      -[:GRANTS]->(:LangSmithPermission {id: 'organization:manage'})
RETURN u.email, r.name
```

Who can read raw agent credentials, since `deployments:read` alone is sufficient:

```cypher
MATCH (u:LangSmithUser)-[:HAS_MEMBERSHIP]->(m:LangSmithWorkspaceMembership)
      -[:HAS_ROLE]->(r:LangSmithRole)-[:GRANTS]->(:LangSmithPermission {id: 'deployments:read'})
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
