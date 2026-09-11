# Azure Queries

## Find Users with the Owner Role

```cypher
MATCH (user:EntraUser)-[:HAS_ROLE_ASSIGNMENT]->(assignment:AzureRoleAssignment)
      -[:ROLE_ASSIGNED]->(role:AzureRoleDefinition)
WHERE role.role_name = "Owner"
RETURN user.email, assignment.scope
```

## Find Principals with Storage Write Access

```cypher
MATCH (assignment:AzureRoleAssignment)-[:ROLE_ASSIGNED]->(role:AzureRoleDefinition)
      -[:HAS_PERMISSIONS]->(permissions:AzurePermissions)
WHERE any(
  action IN permissions.actions
  WHERE action CONTAINS "Microsoft.Storage" AND action CONTAINS "write"
)
RETURN assignment.principal_id, assignment.principal_type, role.role_name,
       assignment.scope
```

## Find High-Privilege Service Principals

```cypher
MATCH (principal:EntraServicePrincipal)-[:HAS_ROLE_ASSIGNMENT]->
      (assignment:AzureRoleAssignment)-[:ROLE_ASSIGNED]->
      (role:AzureRoleDefinition)
WHERE role.role_name IN ["Owner", "Contributor", "User Access Administrator"]
RETURN principal.display_name, role.role_name, assignment.scope
```
