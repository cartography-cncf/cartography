## Entra Schema

### EntraTenant

Representation of an Entra (formerly Azure AD) Tenant.

|Field | Description|
|-------|-------------|
|id | Entra Tenant ID (GUID)|
|created_date_time | Date and time when the tenant was created|
|default_usage_location | Default location for usage reporting|
|deleted_date_time | Date and time when the tenant was deleted (if applicable)|
|display_name | Display name of the tenant|
|marketing_notification_emails | List of email addresses for marketing notifications|
|mobile_device_management_authority | Mobile device management authority for the tenant|
|on_premises_last_sync_date_time | Last time the tenant was synced with on-premises directory|
|on_premises_sync_enabled | Whether on-premises directory sync is enabled|
|partner_tenant_type | Type of partner tenant|
|postal_code | Postal code of the tenant's address|
|preferred_language | Preferred language for the tenant|
|state | State/province of the tenant's address|
|street | Street address of the tenant|
|tenant_type | Type of tenant (e.g., 'AAD')|

### EntraUser

Representation of an Entra [User](https://learn.microsoft.com/en-us/graph/api/user-get?view=graph-rest-1.0&tabs=http).

|Field | Description|
|-------|-------------|
|id | Entra User ID (GUID)|
|user_principal_name | User Principal Name (UPN) of the user|
|display_name | Display name of the user|
|given_name | Given (first) name of the user|
|surname | Surname (last name) of the user|
|email | Primary email address of the user|
|other_mails | Additional email addresses of the user|
|preferred_language | Preferred language of the user|
|preferred_name | Preferred name of the user|
|state | State/province of the user's address|
|usage_location | Location for usage reporting|
|user_type | Type of user|
|show_in_address_list | Whether the user appears in address lists|
|sign_in_sessions_valid_from_date_time | Date and time from which sign-in sessions are valid|
|security_identifier | Security identifier of the user|
|account_enabled | Whether the user account is enabled|
|city | City of the user's address|
|company_name | Company name of the user|
|consent_provided_for_minor | Whether consent was provided for a minor|
|country | Country of the user's address|
|created_date_time | Date and time when the user was created|
|creation_type | Type of user creation|
|deleted_date_time | Date and time when the user was deleted (if applicable)|
|department | Department of the user|
|employee_id | Employee ID of the user|
|employee_type | Type of employee|
|external_user_state | State of external user|
|external_user_state_change_date_time | Date and time when external user state changed|
|hire_date | Hire date of the user|
|is_management_restricted | Whether management is restricted|
|is_resource_account | Whether this is a resource account|
|job_title | Job title of the user|
|last_password_change_date_time | Date and time of last password change|
|mail_nickname | Mail nickname of the user|
|office_location | Office location of the user|
|on_premises_distinguished_name | Distinguished name in on-premises directory|
|on_premises_domain_name | Domain name in on-premises directory|
|on_premises_immutable_id | Immutable ID in on-premises directory|
|on_premises_last_sync_date_time | Last time the user was synced with on-premises directory|
|on_premises_sam_account_name | SAM account name in on-premises directory|
|on_premises_security_identifier | Security identifier in on-premises directory|
|on_premises_sync_enabled | Whether on-premises directory sync is enabled|
|on_premises_user_principal_name | User Principal Name in on-premises directory|

#### Relationships

- All Entra users are linked to an Entra Tenant

    ```cypher
    (:EntraUser)-[:RESOURCE]->(:EntraTenant)
    ```

- Entra users are members of groups

    ```cypher
    (:EntraUser)-[:MEMBER_OF]->(:EntraGroup)
    ```

- Entra users can have app role assignments

    ```cypher
    (:EntraUser)-[:HAS_APP_ROLE]->(:EntraAppRoleAssignment)
    ```


### EntraOU
Representation of an Entra [OU](https://learn.microsoft.com/en-us/graph/api/administrativeunit-get?view=graph-rest-1.0&tabs=http).

|Field | Description|
|-------|-------------|
|id | Entra Administrative Unit (OU) ID (GUID)|
|display_name | Display name of the administrative unit|
|description| Description of the administrative unit|
|membership_type| Membership type ("Assigned" for static or "Dynamic for rule-based)|
|visibility| Visibility setting ("Public" or "Private")|
|is_member_management_restricted | Whether member management is restricted|
|deleted_date_time | Date and time when the administrative unit was soft-deleted |


#### Relationships

- All Entra OUs are linked to an Entra Tenant

    ```cypher
    (:EntraOU)-[:RESOURCE]->(:EntraTenant)
    ```

### EntraGroup
Representation of an Entra [Group](https://learn.microsoft.com/en-us/graph/api/group-get?view=graph-rest-1.0&tabs=http).

|Field | Description|
|-------|-------------|
|id | Entra Group ID (GUID)|
|display_name | Display name of the group|
|description | Description of the group|
|mail | Primary email address of the group|
|mail_nickname | Mail nickname|
|mail_enabled | Whether the group has a mailbox|
|security_enabled | Whether the group is security enabled|
|group_types | List of group types|
|visibility | Group visibility setting|
|is_assignable_to_role | Whether the group can be assigned to roles|
|created_date_time | Creation timestamp|
|deleted_date_time | Deletion timestamp if applicable|

#### Relationships

- All Entra groups are linked to an Entra Tenant

    ```cypher
    (:EntraGroup)-[:RESOURCE]->(:EntraTenant)
    ```

- Entra users are members of groups

    ```cypher
    (:EntraUser)-[:MEMBER_OF]->(:EntraGroup)
    ```

- Entra groups can be members of other groups

    ```cypher
    (:EntraGroup)-[:MEMBER_OF]->(:EntraGroup)
    ```

### EntraApplication

Representation of an Entra [Application](https://learn.microsoft.com/en-us/graph/api/application-get?view=graph-rest-1.0&tabs=http).

|Field | Description|
|-------|-------------|
|id | Entra Application ID (GUID)|
|app_id | Application (client) ID - the unique identifier for the application|
|display_name | Display name of the application|
|publisher_domain | Publisher domain of the application|
|sign_in_audience | Audience that can sign in to the application|
|created_date_time | Date and time when the application was created|
|web_redirect_uris | List of redirect URIs for web applications|
|lastupdated | Timestamp of when this node was last updated in Cartography|

#### Relationships

- All Entra applications are linked to an Entra Tenant

    ```cypher
    (:EntraApplication)-[:RESOURCE]->(:EntraTenant)
    ```

- App role assignments link to applications

    ```cypher
    (:EntraAppRoleAssignment)-[:ASSIGNED_TO]->(:EntraApplication)
    ```

### EntraAppRoleAssignment

Representation of an Entra [App Role Assignment](https://learn.microsoft.com/en-us/graph/api/resources/approleassignment).

|Field | Description|
|-------|-------------|
|id | Unique identifier for the app role assignment|
|app_role_id | The ID of the app role assigned|
|created_date_time | Date and time when the assignment was created|
|principal_id | The ID of the user, group, or service principal assigned the role|
|principal_display_name | Display name of the assigned principal|
|principal_type | Type of principal (User, Group, or ServicePrincipal)|
|resource_display_name | Display name of the resource application|
|resource_id | The service principal ID of the resource application|
|application_app_id | The application ID used for linking to EntraApplication|
|lastupdated | Timestamp of when this node was last updated in Cartography|

#### Relationships

- All app role assignments are linked to an Entra Tenant

    ```cypher
    (:EntraAppRoleAssignment)-[:RESOURCE]->(:EntraTenant)
    ```

- Users can have app role assignments

    ```cypher
    (:EntraUser)-[:HAS_APP_ROLE]->(:EntraAppRoleAssignment)
    ```

- Groups can have app role assignments

    ```cypher
    (:EntraGroup)-[:HAS_APP_ROLE]->(:EntraAppRoleAssignment)
    ```

- App role assignments are linked to applications

    ```cypher
    (:EntraAppRoleAssignment)-[:ASSIGNED_TO]->(:EntraApplication)
    ```

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
