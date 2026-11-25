# LangSmith Queries

## Find agents that can act as users

Lists each agent that holds a user's OAuth token, with the provider and the granted
scopes.

```cypher
MATCH (a:LangSmithAgent)-[:HAS_CREDENTIAL]->(c:LangSmithAgentCredential)
      -[:FOR_PROVIDER]->(p:LangSmithOAuthProvider)
MATCH (c)-[:ON_BEHALF_OF]->(u:LangSmithUser)
RETURN u.email, a.id, p.name, c.scopes, c.expires_at
```

## Find deactivated members who still hold credentials

Lists deactivated members with their unrevoked tokens and the agent credentials that
still act as them.

```cypher
MATCH (u:LangSmithUser)-[:HAS_MEMBERSHIP]->(:LangSmithOrgMembership {is_disabled: true})
OPTIONAL MATCH (u)<-[:OWNED_BY]-(k:LangSmithApiKey) WHERE k.revoked_at IS NULL
OPTIONAL MATCH (u)<-[:ON_BEHALF_OF]-(c:LangSmithAgentCredential)
RETURN u.email, collect(DISTINCT k.short_key), collect(DISTINCT c.id)
```

## Find organization administrators

Includes members who hold `organization:manage` through a custom role.

```cypher
MATCH (u:LangSmithUser)-[:HAS_MEMBERSHIP]->(:LangSmithOrgMembership)
      -[:HAS_ROLE]->(r:LangSmithRole)
      -[:GRANTS]->(:LangSmithPermission {name: 'organization:manage'})
RETURN u.email, r.name
```

## Find who can read agent credentials

`deployments:read` alone is enough to read agent credentials, so this query lists the
members who hold it in each workspace.

```cypher
MATCH (u:LangSmithUser)-[:HAS_MEMBERSHIP]->(m:LangSmithWorkspaceMembership)
      -[:HAS_ROLE]->(r:LangSmithRole)-[:GRANTS]->(:LangSmithPermission {name: 'deployments:read'})
MATCH (m)-[:IN_WORKSPACE]->(w:LangSmithWorkspace)
RETURN w.name, r.name, collect(u.email)
```

## Find who holds a permission through a user group

A user group's role applies to members who also belong to the workspace. Combine this
with the previous query to cover both direct and user group roles.

```cypher
MATCH (u:LangSmithUser)-[:MEMBER_OF]->(g:LangSmithUserGroup)
      -[:HAS_GRANT]->(grant:LangSmithUserGroupGrant)-[:HAS_ROLE]->(r:LangSmithRole)
      -[:GRANTS]->(:LangSmithPermission {name: 'deployments:read'})
MATCH (grant)-[:IN_WORKSPACE]->(w:LangSmithWorkspace)<-[:MEMBER_OF]-(u)
RETURN w.name, g.name, r.name, collect(u.email)
```

## Find access policies that apply through user groups

Lists each policy attached to a user group, with the members it applies to. When
`all_workspaces` is false, the policy applies only in `workspace_ids`. A workspace-scoped
user group's policies apply only in its own workspace.

```cypher
MATCH (p:LangSmithAccessPolicy)-[a:ATTACHED_TO]->(g:LangSmithUserGroup)
OPTIONAL MATCH (u:LangSmithUser)-[:MEMBER_OF]->(g)
RETURN g.name, g.workspace_id, p.name, p.effect, a.all_workspaces, a.workspace_ids,
       collect(u.email)
```

## Find the tags on each deployment and its tracing project

Access policies on the deployment control who can manage it. Policies on its tracing
project control who can read its traces.

```cypher
MATCH (d:LangSmithDeployment)-[:TRACES_TO]->(proj:LangSmithProject)
OPTIONAL MATCH (d)-[:TAGGED]->(dt:LangSmithResourceTag)
OPTIONAL MATCH (proj)-[:TAGGED]->(pt:LangSmithResourceTag)
RETURN d.name, proj.name,
       collect(DISTINCT dt.key + '=' + dt.value) AS deployment_tags,
       collect(DISTINCT pt.key + '=' + pt.value) AS project_tags
```

## Find tracing projects that a tag-based access policy can apply to

Lists each policy that matches on a resource tag, with the projects carrying a tag under
that key. Read `p.condition_summary` for the operator and value. Only `*_if_exists` conditions also
apply to projects without the tag.

```cypher
MATCH (p:LangSmithAccessPolicy)-[:ATTACHED_TO]->(r:LangSmithRole)
UNWIND p.condition_tag_keys AS tag_key
MATCH (w:LangSmithWorkspace)-[:CONTAINS]->(proj:LangSmithProject)
      -[:TAGGED]->(t:LangSmithResourceTag {key: tag_key})
RETURN p.name, p.effect, p.condition_summary, r.name, w.name, proj.name, t.key, t.value
```

## Find untagged tracing projects

Tag-based conditions without `_if_exists` don't match these projects.

```cypher
MATCH (w:LangSmithWorkspace)-[:CONTAINS]->(proj:LangSmithProject)
WHERE NOT (proj)-[:TAGGED]->(:LangSmithResourceTag)
RETURN w.name, proj.name
```

## Find deployments that can be shared outside the organization

```cypher
MATCH (w:LangSmithWorkspace)-[:CONTAINS]->(d:LangSmithDeployment {shareable: true})
RETURN w.name, d.name, d.url
```
