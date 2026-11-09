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

## Find deployments that can be shared outside the organization

```cypher
MATCH (w:LangSmithWorkspace)-[:CONTAINS]->(d:LangSmithDeployment {shareable: true})
RETURN w.name, d.name, d.url
```
