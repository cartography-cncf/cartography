## Workday

Cartography syncs employee and organization data from Workday's HR system, creating a graph of organizational structure and reporting hierarchies.

### Features

- **Employee data** with job information, location, and organizational structure
- **Manager hierarchies** via REPORTS_TO relationships
- **Organization nodes** for departments and teams
- **Human label integration** for cross-module identity queries with Duo, Okta, GitHub, etc.

### Graph Relationships

```
(:WorkdayHuman)-[:MEMBER_OF_ORGANIZATION]->(:WorkdayOrganization)
(:WorkdayHuman)-[:REPORTS_TO]->(:WorkdayHuman)
```

### Configuration

See [Workday Configuration](config.md) for API setup and credentials.

### Schema

See [Workday Schema](schema.md) for node properties, relationships, and sample queries.

### Cross-Module Integration

WorkdayHuman nodes use the `Human` label, enabling identity correlation across modules:

```cypher
// Find all identities for a person
MATCH (h:Human {email: "alice@example.com"})
OPTIONAL MATCH (h:WorkdayHuman)
OPTIONAL MATCH (h)-[:IDENTITY_DUO]->(duo:DuoUser)
RETURN h.name, h.title, duo.username
```

### Security and Privacy

Employee data contains PII (names, emails, organizational data). Ensure:
- Neo4j database is secured with authentication
- Access controls limit who can query employee data
- API credentials are read-only and stored in environment variables only

```{toctree}
config
schema
examples
```
