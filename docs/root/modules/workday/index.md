## Workday

Cartography can sync employee and organization data from Workday's HR system.

### Module Features

- **Employee Data**: Comprehensive employee information including contact details, job information, and organizational structure
- **Organizations**: Supervisory organization/department data
- **Manager Hierarchy**: Reporting relationships (who reports to whom)
- **Human Identity Integration**: WorkdayHuman nodes include the `Human` label for integration with other identity systems (Duo, Okta, GitHub, etc.)

### Data Collected

#### WorkdayHuman Nodes
- Employee identification (ID, name, email)
- Job information (title, worker type)
- Location and country
- Organizational structure (function, sub-function, team, sub-team)
- Cost center and company
- Source tracking

#### WorkdayOrganization Nodes
- Organization/department names
- Automatically extracted from employee data

### Graph Relationships

```
(:WorkdayHuman)-[:MEMBER_OF_ORGANIZATION]->(:WorkdayOrganization)
(:WorkdayHuman)-[:REPORTS_TO]->(:WorkdayHuman)
```

### Identity Integration

WorkdayHuman nodes use the `Human` label, enabling queries across identity systems:

```cypher
// Find all identities for a person
MATCH (h:Human {email: "alice@example.com"})
OPTIONAL MATCH (h:WorkdayHuman)
OPTIONAL MATCH (h)-[:IDENTITY_DUO]->(duo:DuoUser)
OPTIONAL MATCH (h)-[:IDENTITY_OKTA]->(okta:OktaUser)
RETURN h.name, h.email, h.title,
       duo.username as duo_account,
       okta.username as okta_account
```

### Configuration

See [Workday Configuration](config.md) for setup instructions.

### Schema

See [Workday Schema](schema.md) for detailed schema documentation and sample queries.

### Use Cases

- **Organizational Analysis**: Understand team structures and reporting hierarchies
- **Access Reviews**: Identify employees in specific organizations or locations for access reviews
- **Cross-System Correlation**: Link Workday HR data with technical access (Duo, AWS, GitHub)
- **Manager Identification**: Find managers and their direct/indirect reports
- **Team Mapping**: Analyze team composition and organizational structure

### Privacy and Security

The Workday module handles sensitive employee data. Security considerations:

- **PII Protection**: Employee names, emails, and organizational data are personally identifiable
- **Database Security**: Secure your Neo4j instance with authentication and encryption
- **Access Control**: Limit who can query the Workday data in Neo4j
- **Credential Storage**: API passwords are handled via environment variables, never stored in code
- **API Security**: Uses HTTPS with HTTP Basic Authentication
