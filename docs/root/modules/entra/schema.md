## Entra Schema

### EntraTenant

Representation of an Entra (formerly Azure AD) Tenant.

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for organizational tenants across different systems (e.g., OktaOrganization, AWSAccount, GCPOrganization).

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

> **Ontology Mapping**: This node has the extra label `UserAccount` to enable cross-platform queries for user accounts across different systems (e.g., OktaUser, AWSSSOUser, GitHubUser).

|Field | Description|
|-------|-------------|
|id | Entra User ID (GUID)|
|user_principal_name | User Principal Name (UPN) of the user|
|display_name | Display name of the user|
|given_name | Given (first) name of the user|
|surname | Surname (last name) of the user|
|email | Primary email address of the user|
|mobile_phone | Mobile phone number of the user|
|business_phones | Business phone numbers of the user|
|job_title | Job title of the user|
|department | Department of the user|
|office_location | Office location of the user|
|city | City of the user's address|
|state | State/province of the user's address|
|country | Country of the user's address|
|company_name | Company name of the user|
|preferred_language | Preferred language of the user|
|employee_id | Employee ID of the user|
|employee_type | Type of employee|
|account_enabled | Whether the user account is enabled|
|age_group | Age group of the user|
|manager_id | ID of the user's manager|

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

- Entra users can have a manager

    ```cypher
    (:EntraUser)-[:REPORTS_TO]->(:EntraUser)
    ```

- Entra users can be owners of groups

    ```cypher
    (:EntraUser)-[:OWNER_OF]->(:EntraGroup)
    ```

- Entra users can sign on to AWSSSOUser via SAML federation to AWS Identity Center. See https://docs.aws.amazon.com/singlesignon/latest/userguide/idp-microsoft-entra.html and https://learn.microsoft.com/en-us/entra/identity/saas-apps/aws-single-sign-on-tutorial.
    ```
    (:EntraUser)-[:CAN_SIGN_ON_TO]->(:AWSSSOUser)
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

> **Ontology Mapping**: This node has the extra label `UserGroup` to enable cross-platform queries for user groups across different systems (e.g., AWSGroup, EntraGroup, GoogleWorkspaceGroup).

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

- Entra groups can have owners

    ```cypher
    (:EntraGroup)-[:OWNER_OF]->(:EntraUser)
    ```

### EntraApplication

Representation of an Entra [Application](https://learn.microsoft.com/en-us/graph/api/application-get?view=graph-rest-1.0&tabs=http).

> **Ontology Mapping**: This node has the extra label `ThirdPartyApp` to enable cross-platform queries for OAuth/SAML applications across different systems (e.g., OktaApplication, KeycloakClient).

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

- An Entra service principal is an instance of an Entra application deployed in an Entra tenant

    ```cypher
    (:EntraServicePrincipal)<-[:SERVICE_PRINCIPAL]-(:EntraApplication)
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

### EntraServicePrincipal

Representation of an Entra [Service Principal](https://learn.microsoft.com/en-us/graph/api/serviceprincipal-get?view=graph-rest-1.0&tabs=http).

|Field | Description|
|-------|-------------|
|id | Entra Service Principal ID (GUID)|
|app_id | Application (client) ID - the unique identifier for the application|
|display_name | Display name of the service principal|
|reply_urls | List of reply URLs for the service principal|
|aws_identity_center_instance_id | AWS Identity Center instance ID extracted from reply URLs|
|account_enabled | Whether the service principal account is enabled|
|service_principal_type | Type of service principal (Application, ManagedIdentity, etc.)|
|app_owner_organization_id | Organization ID that owns the application|
|deleted_date_time | Date and time when the service principal was deleted (if applicable)|
|homepage | Homepage URL of the application|
|logout_url | Logout URL for the application|
|preferred_single_sign_on_mode | Preferred single sign-on mode|
|preferred_token_signing_key_thumbprint | Thumbprint of the preferred token signing key|
|sign_in_audience | Audience that can sign in to the application|
|tags | Tags associated with the service principal|
|token_encryption_key_id | Key ID used for token encryption|
|lastupdated | Timestamp of when this node was last updated in Cartography|

#### Relationships

- All Entra service principals are scoped to an Entra Tenant

    ```cypher
    (:EntraServicePrincipal)-[:RESOURCE]->(:EntraTenant)
    ```

- An Entra service principal is an instance of an Entra application deployed in an Entra tenant

    ```cypher
    (:EntraServicePrincipal)<-[:SERVICE_PRINCIPAL]-(:EntraApplication)
    ```

- Service principals can federate to AWS Identity Center via SAML

    ```cypher
    (:EntraServicePrincipal)-[:FEDERATES_TO]->(:AWSIdentityCenter)
    ```

### IntuneManagedDevice

Representation of a [Managed Device](https://learn.microsoft.com/en-us/graph/api/resources/intune-devices-manageddevice?view=graph-rest-1.0) enrolled in Intune.

> **Ontology Mapping**: This node participates in the `Device` ontology via the `entra` device mapping, allowing canonical `Device` nodes to be linked to Intune-managed devices by shared identifiers such as serial number.

| Field | Description |
|-------|-------------|
| **id** | Unique identifier for the managed device |
| device_name | Name of the device |
| user_id | ID of the user associated with the device |
| user_principal_name | UPN of the user associated with the device |
| managed_device_owner_type | Ownership type: `company` or `personal` |
| operating_system | Operating system (e.g., Windows, macOS, iOS) |
| os_version | Operating system version |
| compliance_state | Compliance state: `compliant`, `noncompliant`, `conflict`, `error`, `inGracePeriod`, `configManager`, `unknown` |
| is_encrypted | Whether the device is encrypted |
| jail_broken | Whether the device is jail broken or rooted |
| management_agent | Management channel (e.g., `mdm`, `eas`) |
| manufacturer | Device manufacturer |
| model | Device model |
| serial_number | Serial number |
| imei | IMEI identifier |
| meid | MEID identifier |
| wifi_mac_address | Wi-Fi MAC address |
| ethernet_mac_address | Ethernet MAC address |
| azure_ad_device_id | Azure AD device ID |
| azure_ad_registered | Whether registered in Azure AD |
| device_enrollment_type | How the device was enrolled |
| device_registration_state | Device registration state |
| is_supervised | Whether the device is supervised |
| enrolled_date_time | When the device was enrolled |
| last_sync_date_time | Last successful sync with Intune |
| eas_activated | Whether Exchange ActiveSync is activated |
| eas_device_id | Exchange ActiveSync device ID |
| partner_reported_threat_state | Threat state from Mobile Threat Defense partner |
| total_storage_space_in_bytes | Total storage in bytes |
| free_storage_space_in_bytes | Free storage in bytes |
| physical_memory_in_bytes | Physical memory in bytes |
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- Intune managed devices belong to a tenant

    ```cypher
    (:IntuneManagedDevice)-[:RESOURCE]->(:EntraTenant)
    ```

- Entra users enroll devices in Intune

    ```cypher
    (:EntraUser)-[:ENROLLED_TO]->(:IntuneManagedDevice)
    ```

### IntuneDetectedApp

Representation of a [Detected App](https://learn.microsoft.com/en-us/graph/api/resources/intune-devices-detectedapp?view=graph-rest-1.0) discovered on managed devices.

| Field | Description |
|-------|-------------|
| **id** | Unique identifier for the detected app |
| display_name | Name of the discovered application |
| version | Version of the application |
| device_count | Number of devices with this app installed |
| publisher | Publisher of the application |
| platform | Platform: `windows`, `ios`, `macOS`, `chromeOS`, etc. |
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- Detected apps belong to a tenant

    ```cypher
    (:IntuneDetectedApp)-[:RESOURCE]->(:EntraTenant)
    ```

- Managed devices have detected apps installed

    ```cypher
    (:IntuneManagedDevice)-[:HAS_APP]->(:IntuneDetectedApp)
    ```

### IntuneCompliancePolicy

Representation of a [Device Compliance Policy](https://learn.microsoft.com/en-us/graph/api/resources/intune-deviceconfig-devicecompliancepolicy?view=graph-rest-1.0) configured in Intune.

| Field | Description |
|-------|-------------|
| **id** | Unique identifier for the compliance policy |
| display_name | Admin-provided name of the policy |
| description | Admin-provided description |
| platform | Target platform (derived from `@odata.type`) |
| version | Version of the policy |
| created_date_time | When the policy was created |
| last_modified_date_time | When the policy was last modified |
| applies_to_all_users | Whether the policy is assigned to all licensed users |
| applies_to_all_devices | Whether the policy is assigned to all managed devices |
| firstseen | Timestamp of when a sync job first created this node |
| lastupdated | Timestamp of the last time the node was updated |

#### Relationships

- Compliance policies belong to a tenant

    ```cypher
    (:IntuneCompliancePolicy)-[:RESOURCE]->(:EntraTenant)
    ```

- Compliance policies are assigned to Entra groups

    ```cypher
    (:IntuneCompliancePolicy)-[:ASSIGNED_TO]->(:EntraGroup)
    ```

- Compliance policies apply to managed devices (resolved by analysis job)

    ```cypher
    (:IntuneCompliancePolicy)-[:APPLIES_TO]->(:IntuneManagedDevice)
    ```

    The `APPLIES_TO` relationship is not ingested directly from the API — it is computed by the `intune_compliance_policy_device` analysis job using the following logic:

    1. **Group assignment**: If the policy is assigned to an `EntraGroup` via `ASSIGNED_TO`, any `EntraUser` who is a `MEMBER_OF` that group and has `ENROLLED_TO` a managed device receives the policy.

        ```cypher
        (:IntuneCompliancePolicy)-[:ASSIGNED_TO]->(:EntraGroup)<-[:MEMBER_OF]-(:EntraUser)-[:ENROLLED_TO]->(:IntuneManagedDevice)
        ```

    2. **All users**: If `policy.applies_to_all_users = true`, the policy applies to every managed device in the tenant that has at least one enrolled user.

    3. **All devices**: If `policy.applies_to_all_devices = true`, the policy applies to every managed device in the tenant regardless of user enrollment.

    Stale `APPLIES_TO` relationships are deleted at the end of each run, scoped to the current tenant so that edges belonging to other tenants are not affected. Resolution only considers policies and devices refreshed in the current sync so partial Intune permission coverage does not preserve stale policy-to-device links.
