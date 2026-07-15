## Microsoft Examples

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

### Intune compliance policy resolution

The `Intune compliance policy to device resolution` analysis job creates
`(:IntuneCompliancePolicy)-[:APPLIES_TO]->(:IntuneManagedDevice)` relationships.
It applies a policy to:

1. Devices enrolled by users who belong to an assigned Entra group.
1. Every enrolled user's device when `applies_to_all_users` is true.
1. Every managed device in the tenant when `applies_to_all_devices` is true.

The job only considers policies and devices refreshed during the current tenant
sync. It removes stale `APPLIES_TO` relationships within that tenant after
creating current relationships.

### Microsoft Graph references

- [User](https://learn.microsoft.com/en-us/graph/api/user-get?view=graph-rest-1.0&tabs=http)
- [Administrative unit](https://learn.microsoft.com/en-us/graph/api/administrativeunit-get?view=graph-rest-1.0&tabs=http)
- [Group](https://learn.microsoft.com/en-us/graph/api/group-get?view=graph-rest-1.0&tabs=http)
- [Application](https://learn.microsoft.com/en-us/graph/api/application-get?view=graph-rest-1.0&tabs=http)
- [App role assignment](https://learn.microsoft.com/en-us/graph/api/resources/approleassignment)
- [Service principal](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-get?view=graph-rest-1.0&tabs=http)
- [Directory role definition](https://learn.microsoft.com/en-us/graph/api/resources/unifiedroledefinition)
- [Directory role assignment](https://learn.microsoft.com/en-us/graph/api/resources/unifiedroleassignment)
- [Intune managed device](https://learn.microsoft.com/en-us/graph/api/resources/intune-devices-manageddevice?view=graph-rest-1.0)
- [Intune detected app](https://learn.microsoft.com/en-us/graph/api/resources/intune-devices-detectedapp?view=graph-rest-1.0)
- [Intune device compliance policy](https://learn.microsoft.com/en-us/graph/api/resources/intune-deviceconfig-devicecompliancepolicy?view=graph-rest-1.0)
- [Microsoft Entra federation with AWS Identity Center](https://learn.microsoft.com/en-us/entra/identity/saas-apps/aws-single-sign-on-tutorial)
- [AWS Identity Center external identity provider setup](https://docs.aws.amazon.com/singlesignon/latest/userguide/idp-microsoft-entra.html)
