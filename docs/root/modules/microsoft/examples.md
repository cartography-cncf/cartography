# Microsoft Examples

Here are some common query patterns for working with Microsoft Entra applications and access management.

### Application Access Analysis

**Find all users with access to a specific application:**
```cypher
MATCH (u:EntraUser)-[:HAS_APP_ROLE]->(ara:EntraAppRoleAssignment)-[:ASSIGNED_TO]->(app:EntraApplication)
WHERE app.display_name = "Finance Tracker"
RETURN u.display_name, u.user_principal_name, ara.created_date_time
ORDER BY ara.created_date_time DESC
```

**Find all applications a user has access to:**
```cypher
MATCH (u:EntraUser)-[:HAS_APP_ROLE]->(ara:EntraAppRoleAssignment)-[:ASSIGNED_TO]->(app:EntraApplication)
WHERE u.user_principal_name = "john.doe@example.com"
RETURN app.display_name, app.app_id, ara.app_role_id, ara.created_date_time
ORDER BY app.display_name
```

**Find users with access via group membership:**
```cypher
MATCH (u:EntraUser)-[:MEMBER_OF]->(g:EntraGroup)-[:HAS_APP_ROLE]->(ara:EntraAppRoleAssignment)-[:ASSIGNED_TO]->(app:EntraApplication)
WHERE app.display_name = "HR Portal"
RETURN u.display_name, u.user_principal_name, g.display_name as group_name, ara.created_date_time
ORDER BY u.display_name
```

### Defender for Endpoint

**Find unresolved high-severity Defender alerts with the affected machine and its enrolled user:**
```cypher
MATCH (a:DefenderAlert)-[:AFFECTS]->(m:DefenderMachine)
WHERE a.severity = "high"
OPTIONAL MATCH (m)-[:ASSOCIATED_WITH]->(:IntuneManagedDevice)<-[:ENROLLED_TO]-(u:EntraUser)
RETURN a.title, a.created_date_time, m.computer_dns_name, u.user_principal_name
ORDER BY a.created_date_time DESC
```

**Find Defender machines that aren't onboarded:**
```cypher
MATCH (m:DefenderMachine)
WHERE m.onboarding_status <> "Onboarded"
RETURN m.computer_dns_name, m.onboarding_status, m.last_seen
ORDER BY m.last_seen DESC
```

### Vendor apps users consented to with access to their mail

```cypher
MATCH (u:EntraUser)-[auth:AUTHORIZED]->(sp:EntraServicePrincipal:ThirdPartyApp)
WHERE ANY(scope IN auth.scopes WHERE scope STARTS WITH 'https://graph.microsoft.com/Mail.')
RETURN sp.display_name AS app, count(u) AS users, collect(DISTINCT u.user_principal_name)[..10] AS sample
ORDER BY users DESC
```
