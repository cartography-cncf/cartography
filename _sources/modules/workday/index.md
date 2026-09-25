# Workday

Cartography syncs employee and organization data from Workday's HR system, creating a graph of organizational structure and reporting hierarchies.

## Features

- **Employee data** with job information, location, and organizational structure
- **Manager hierarchies** via REPORTS_TO relationships
- **Organization nodes** for departments and teams
- **Human label integration** for cross-module identity queries with Duo, Okta, GitHub, etc.

## Graph Relationships

```
(:WorkdayHuman)-[:MEMBER_OF_ORGANIZATION]->(:WorkdayOrganization)
(:WorkdayHuman)-[:REPORTS_TO]->(:WorkdayHuman)
```

## Cross-Module Integration

WorkdayHuman nodes use the `Human` label, enabling identity correlation across modules:

## Security and Privacy

Employee data contains PII (names, emails, organizational data). Ensure:
- Neo4j database is secured with authentication
- Access controls limit who can query employee data
- API credentials are read-only and stored in environment variables only

See [configuration](config.md) for API setup and credentials,
[examples](examples.md) for sample queries, and the generated
[schema](schema.md) for fields and relationships.

```{toctree}
config
schema
examples
```
