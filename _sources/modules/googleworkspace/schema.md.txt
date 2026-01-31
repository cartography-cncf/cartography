## Google Workspace Schema

```mermaid
graph LR
    T(GoogleWorkspaceTenant) -- RESOURCE --> U(GoogleWorkspaceUser)
    T -- RESOURCE --> G(GoogleWorkspaceGroup)
    T -- RESOURCE --> D(GoogleWorkspaceDevice)
    T -- RESOURCE --> A(GoogleWorkspaceOAuthApp)
    U -- MEMBER_OF --> G
    U -- OWNER_OF --> G
    U -- OWNS --> D
    U -- "AUTHORIZED {scopes}" --> A
    U -. INHERITED_MEMBER_OF .-> G
    U -. INHERITED_OWNER_OF .-> G
    G -- MEMBER_OF --> G
    G -- OWNER_OF --> G
    G -. INHERITED_MEMBER_OF .-> G
    G -. INHERITED_OWNER_OF .-> G
```

**Note:** Dashed lines represent inherited relationships that are computed automatically based on group hierarchy.


### GoogleWorkspaceTenant
Represents a Google Workspace tenant (customer account).

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for organizational tenants across different systems (e.g., OktaOrganization, AWSAccount).

| Field | Description |
|-------|-------------|
| id | The unique ID for the Google Workspace customer account. A customer id can be used
| domain | The primary domain name for the Google Workspace customer account.
| name | The name of the organization associated with the Google Workspace customer account.
| lastupdated | Timestamp of when a sync job last updated this node
| firstseen | Timestamp of when a sync job first discovered this node

#### Node Labels
- `GoogleWorkspaceTenant`

#### Relationships
- Tenant has users:
    ```
    (:GoogleWorkspaceTenant)-[:RESOURCE]->(:GoogleWorkspaceUser)
    ```
- Tenant has groups:
    ```
    (:GoogleWorkspaceTenant)-[:RESOURCE]->(:GoogleWorkspaceGroup)
    ```
- Tenant has devices:
    ```
    (:GoogleWorkspaceTenant)-[:RESOURCE]->(:GoogleWorkspaceDevice)
    ```
- Tenant has OAuth apps:
    ```
    (:GoogleWorkspaceTenant)-[:RESOURCE]->(:GoogleWorkspaceOAuthApp)
    ```


### GoogleWorkspaceUser

Reference:
https://developers.google.com/admin-sdk/directory/v1/reference/users#resource

> **Ontology Mapping**: This node has the extra label `UserAccount` to enable cross-platform queries for user accounts across different systems (e.g., GitHubUser, DuoUser, SlackUser).

| Field | Description |
|-------|--------------|
| id | The unique ID for the user as a string. A user id can be used as a user request URI's userKey
| user_id | duplicate of id.
| agreed_to_terms |  This property is true if the user has completed an initial login and accepted the Terms of Service agreement.
| change_password_at_next_login | Indicates if the user is forced to change their password at next login. This setting doesn't apply when the user signs in via a third-party identity provider.
| creation_time | The time the user's account was created. The value is in ISO 8601 date and time format. The time is the complete date plus hours, minutes, and seconds in the form YYYY-MM-DDThh:mm:ssTZD. For example, 2010-04-05T17:30:04+01:00.
| customer_id | The customer ID to retrieve all account users.  You can use the alias my_customer to represent your account's customerId.  As a reseller administrator, you can use the resold customer account's customerId. To get a customerId, use the account's primary domain in the domain parameter of a users.list request.
| etag | ETag of the resource
| include_in_global_address_list | Indicates if the user's profile is visible in the Google Workspace global address list when the contact sharing feature is enabled for the domain. For more information about excluding user profiles, see the administration help center.
| ip_whitelisted | If true, the user's IP address is white listed.
| is_admin | Indicates a user with super admininistrator privileges. The isAdmin property can only be edited in the Make a user an administrator operation (makeAdmin method). If edited in the user insert or update methods, the edit is ignored by the API service.
| is_delegated_admin | Indicates if the user is a delegated administrator.  Delegated administrators are supported by the API but cannot create or undelete users, or make users administrators. These requests are ignored by the API service.  Roles and privileges for administrators are assigned using the Admin console.
| is_enforced_in_2_sv | Is 2-step verification enforced (Read-only)
| is_enrolled_in_2_sv | Is enrolled in 2-step verification (Read-only)
| is_mailbox_setup | Indicates if the user's Google mailbox is created. This property is only applicable if the user has been assigned a Gmail license.
| kind | The type of the API resource. For Users resources, the value is admin#directory#user.
| last_login_time | The last time the user logged into the user's account. The value is in ISO 8601 date and time format. The time is the complete date plus hours, minutes, and seconds in the form YYYY-MM-DDThh:mm:ssTZD. For example, 2010-04-05T17:30:04+01:00.
| name | First name + Last name
| family_name | The user's last name. Required when creating a user account.
| given_name | The user's first name. Required when creating a user account.
| org_unit_path | The full path of the parent organization associated with the user. If the parent organization is the top-level, it is represented as a forward slash (/).
| primary_email | The user's primary email address. This property is required in a request to create a user account. The primaryEmail must be unique and cannot be an alias of another user.
| suspended | Indicates if user is suspended
| archived | Indicates if user is archived
| thumbnail_photo_etag | ETag of the user's photo
| thumbnail_photo_url | Photo Url of the user
| organization_name | Name of the user's primary organization
| organization_title | Title of the user in their primary organization
| organization_department | Department of the user in their primary organization
| lastupdated | Timestamp of when a sync job last updated this node
| firstseen | Timestamp of when a sync job first discovered this node

#### Node Labels

- `GoogleWorkspaceUser`
- `UserAccount`
- `GCPPrincipal`

#### Relationships
- GoogleTenant has users:

    ```
    (:GoogleWorkspaceTenant)-[:RESOURCE]->(:GoogleWorkspaceUser)
    ```

- User belongs to groups:

    ```
    (GoogleWorkspaceUser)-[MEMBER_OF]->(GoogleWorkspaceGroup)
    ```

- User owns group:

    ```
    (GoogleWorkspaceUser)-[OWNER_OF]->(GoogleWorkspaceGroup)
    ```

- User owns device:

    ```
    (GoogleWorkspaceUser)-[OWNS]->(GoogleWorkspaceDevice)
    ```

- User has inherited membership in group (through group hierarchy):

    ```
    (GoogleWorkspaceUser)-[INHERITED_MEMBER_OF]->(GoogleWorkspaceGroup)
    ```

- User has inherited ownership of group (through group hierarchy):

    ```
    (GoogleWorkspaceUser)-[INHERITED_OWNER_OF]->(GoogleWorkspaceGroup)
    ```

- User has authorized OAuth apps:

    ```
    (GoogleWorkspaceUser)-[AUTHORIZED {scopes: [...]}]->(GoogleWorkspaceOAuthApp)
    ```


### GoogleWorkspaceGroup

Reference:
https://developers.google.com/admin-sdk/directory/v1/reference/groups


| Field | Description |
|-------|--------------|
| id | The unique ID of a group. A group id can be used as a group request URI's groupKey.
| group_id | duplicate of id.
| admin_created | Value is true if this group was created by an administrator rather than a user.
| description |  An extended description to help users determine the purpose of a group. For example, you can include information about who should join the group, the types of messages to send to the group, links to FAQs about the group, or related groups. Maximum length is 4,096 characters.
| direct_members_count | The number of users that are direct members of the group. If a group is a member (child) of this group (the parent), members of the child group are not counted in the directMembersCount property of the parent group
| email | The group's email address. If your account has multiple domains, select the appropriate domain for the email address. The email must be unique. This property is required when creating a group. Group email addresses are subject to the same character usage rules as usernames, see the administration help center for the details.
| etag | ETag of the resource
| kind | The type of the API resource. For Groups resources, the value is admin#directory#group.
| name | The group's display name.
| lastupdated | Timestamp of when a sync job last updated this node
| firstseen | Timestamp of when a sync job first discovered this node

#### Node Labels

- `GoogleWorkspaceGroup`
- `GCPPrincipal`

#### Relationships
- GoogleTenant has groups:

    ```
    (:GoogleWorkspaceTenant)-[:RESOURCE]->(:GoogleWorkspaceGroup)
    ```

- GoogleWorkspaceGroup can have members that are GoogleWorkspaceUsers.

    ```
    (GoogleWorkspaceUser)-[MEMBER_OF]->(GoogleWorkspaceGroup)
    ```

- GoogleWorkspaceGroup can have owners that are GoogleWorkspaceUsers.

    ```
    (GoogleWorkspaceUser)-[OWNER_OF]->(GoogleWorkspaceGroup)
    ```

- Group can be member of another group:

    ```
    (GoogleWorkspaceGroup)-[MEMBER_OF]->(GoogleWorkspaceGroup)
    ```

- Group can own another group:

    ```
    (GoogleWorkspaceGroup)-[OWNER_OF]->(GoogleWorkspaceGroup)
    ```

- Group has inherited membership in another group (through group hierarchy):

    ```
    (GoogleWorkspaceGroup)-[INHERITED_MEMBER_OF]->(GoogleWorkspaceGroup)
    ```


- Group has inherited ownership of another group (through group hierarchy):

    ```
    (GoogleWorkspaceGroup)-[INHERITED_OWNER_OF]->(GoogleWorkspaceGroup)
    ```


### GoogleWorkspaceDevice

Represents a device managed by Google Workspace.

> **Ontology Mapping**: This node has the extra label `Device` to enable cross-platform queries for devices across different systems (e.g., BigfixComputer, CrowdstrikeHost, KandjiDevice).

| Field | Description |
|-------|-------------|
| id | Unique device identifier (deviceId) |
| lastupdated | Timestamp of when a sync job last updated this node |
| hostname | Device hostname (indexed) |
| model | Device model |
| manufacturer | Device manufacturer |
| release_version | Device release version |
| brand | Device brand |
| build_number | Device build number |
| kernel_version | Device kernel version |
| baseband_version | Device baseband version |
| device_type | Type of device (ANDROID, MAC_OS, etc.) |
| os_version | Operating system version |
| owner_type | Device ownership type (BYOD, etc.) |
| serial_number | Device serial number |
| asset_tag | Asset tag assigned to device |
| imei | International Mobile Equipment Identity |
| meid | Mobile Equipment Identifier |
| wifi_mac_addresses | WiFi MAC addresses |
| network_operator | Network operator |
| encryption_state | Device encryption status |
| compromised_state | Device security compromise status |
| management_state | Device management status |
| create_time | Device creation timestamp |
| last_sync_time | Last synchronization timestamp |
| security_patch_time | Security patch timestamp |
| android_specific_attributes | Android-specific device attributes |
| enabled_developer_options | Whether developer options are enabled |
| enabled_usb_debugging | Whether USB debugging is enabled |
| bootloader_version | Bootloader version |
| other_accounts | Other accounts on the device |
| unified_device_id | Unified device identifier |
| endpoint_verification_specific_attributes | Endpoint verification attributes |
| customer_id | The Google Workspace customer ID |

#### Relationships

- Device belongs to tenant:

    ```
    (:GoogleWorkspaceDevice)<-[:RESOURCE]-(:GoogleWorkspaceTenant)
    ```

- User owns device:

    ```
    (:GoogleWorkspaceUser)-[:OWNS]->(:GoogleWorkspaceDevice)
    ```


### GoogleWorkspaceOAuthApp

Represents third-party OAuth applications that have been authorized by users in the Google Workspace organization.

Reference:
https://developers.google.com/workspace/admin/directory/reference/rest/v1/tokens

> **Ontology Mapping**: This node has the extra label `ThirdPartyApp` to enable cross-platform queries for OAuth applications across different systems (e.g., OktaApplication, EntraApplication).

| Field | Description |
|-------|-------------|
| id | Unique identifier for the app (equal to client_id) |
| client_id | The Client ID of the application (indexed) |
| display_text | The displayable name of the application |
| anonymous | Whether the application is granted access anonymously |
| native_app | Whether this is a native/installed application |
| customer_id | The Google Workspace customer ID |
| lastupdated | Timestamp of when a sync job last updated this node |
| firstseen | Timestamp of when a sync job first discovered this node |

#### Relationships

- App belongs to tenant:

    ```
    (:GoogleWorkspaceOAuthApp)<-[:RESOURCE]-(:GoogleWorkspaceTenant)
    ```

- User authorized app (with scopes on the relationship):

    ```
    (:GoogleWorkspaceUser)-[:AUTHORIZED {scopes: [...]}]->(:GoogleWorkspaceOAuthApp)
    ```

    The `AUTHORIZED` relationship includes a `scopes` property containing the list of OAuth scopes granted by the user to the application.
