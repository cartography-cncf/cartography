# LangSmith

The LangSmith module ingests the identity, access-control and agent-credential surface of
[LangSmith](https://docs.langchain.com/langsmith/) and LangGraph Platform: who can do
what, and which agents hold which user's OAuth tokens. See the generated
[LangSmith schema](schema.md) for the available properties and relationships.

```{toctree}
config
schema
```

## Example queries

Which agents can act as which users, against which provider, and with which scopes:

```cypher
MATCH (a:LangSmithAgent)-[:HAS_CREDENTIAL]->(c:LangSmithAgentCredential)
      -[:FOR_PROVIDER]->(p:LangSmithOAuthProvider)
MATCH (c)-[:ON_BEHALF_OF]->(u:LangSmithUser)
RETURN u.email, a.id, p.name, c.scopes, c.expires_at
```

Deactivated members who still hold live tokens, and the agents that still act as them:

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

Who can read agent credentials in each workspace, because `deployments:read` alone is
enough:

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
