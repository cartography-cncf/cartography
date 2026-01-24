## Example Queries

Here are some common query patterns for working with Entra applications and access management:

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
