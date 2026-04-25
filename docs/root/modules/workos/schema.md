## WorkOS Schema

```mermaid
graph LR
E(WorkOSEnvironment) -- RESOURCE --> O(Organization)
E -- RESOURCE --> U(User)
E -- RESOURCE --> D(Directory)
E -- RESOURCE --> R(Role)
E -- RESOURCE --> I(Invitation)
E -- RESOURCE --> M(OrganizationMembership)
E -- RESOURCE --> DU(DirectoryUser)
E -- RESOURCE --> DG(DirectoryGroup)
E -- RESOURCE --> OD(OrganizationDomain)
E -- RESOURCE --> AK(APIKey)
E -- RESOURCE --> APP(Application)
E -- RESOURCE --> ACS(AppClientSecret)
APP -- HAS_SECRET --> ACS
APP -- BELONGS_TO --> O
O -- HAS --> R
O -- OWNS --> AK
U -- MEMBER_OF --> M
M -- IN --> O
M -- WITH_ROLE --> R
I -- FOR_ORGANIZATION --> O
I -- INVITES --> U
I -- INVITED_BY --> U
D -- BELONGS_TO --> O
D -- HAS --> DU
D -- HAS --> DG
DU -- BELONGS_TO --> O
DU -- MEMBER_OF --> DG
DG -- BELONGS_TO --> O
OD -- DOMAIN_OF --> O
```


### WorkOSEnvironment

Represents a WorkOS Environment (root node for a WorkOS account/client). This is the top-level node that all other WorkOS resources are connected to.

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for organizational tenants across different systems (e.g., OktaOrganization, AzureTenant, GCPOrganization).


| Field | Description |
|-------|-------------|
| id | The WorkOS client ID |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |

#### Relationships
- All WorkOS resources belong to an `Environment`
    ```
    (WorkOSEnvironment)-[:RESOURCE]->(
        :WorkOSOrganization,
        :WorkOSUser,
        :WorkOSDirectory,
        :WorkOSRole,
        :WorkOSInvitation,
        :WorkOSOrganizationMembership,
        :WorkOSDirectoryUser,
        :WorkOSDirectoryGroup,
        :WorkOSOrganizationDomain,
        :WorkOSAPIKey,
        :WorkOSApplication,
        :WorkOSApplicationClientSecret)
    ```


### WorkOSOrganization

Represents a WorkOS Organization. Organizations are the primary tenant unit in WorkOS and can contain multiple users, directories, and other resources.

**Ontology Labels**: `Tenant`

| Field | Description |
|-------|-------------|
| id | The identifier, which can be referenced in API endpoints |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| name | The name of the organization |
| created_at | The RFC 3339 datetime of when the organization was created |
| updated_at | The RFC 3339 datetime of when the organization was last updated |
| allow_profiles_outside_organization | Whether profiles outside the organization are allowed |

#### Relationships
- `Organization` belongs to an `Environment`
    ```
    (WorkOSEnvironment)-[:RESOURCE]->(WorkOSOrganization)
    ```
- `Organization` has `Roles`
    ```
    (WorkOSOrganization)-[:HAS]->(WorkOSRole)
    ```


### WorkOSUser

Represents an individual user in WorkOS. Users can be members of multiple organizations and have authentication profiles.

> **Ontology Mapping**: This node has the extra label `UserAccount` to enable cross-platform queries for user accounts across different systems (e.g., OktaUser, EntraUser, GitHubUser).

| Field | Description |
|-------|-------------|
| id | The identifier, which can be referenced in API endpoints |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| email | The email address of the user |
| first_name | The first name of the user |
| last_name | The last name of the user |
| email_verified | Whether the email address has been verified |
| profile_picture_url | URL to the user's profile picture |
| last_sign_in_at | The RFC 3339 datetime of the user's last sign-in |
| created_at | The RFC 3339 datetime of when the user was created |
| updated_at | The RFC 3339 datetime of when the user was last updated |

#### Relationships
- `User` belongs to an `Environment`
    ```
    (WorkOSEnvironment)-[:RESOURCE]->(WorkOSUser)
    ```
- `User` is member of `OrganizationMembership`
    ```
    (WorkOSUser)-[:MEMBER_OF]->(WorkOSOrganizationMembership)
    ```
- `User` can be invited by `Invitation`
    ```
    (WorkOSInvitation)-[:INVITES]->(WorkOSUser)
    ```
- `User` can create `Invitation`
    ```
    (WorkOSInvitation)-[:INVITED_BY]->(WorkOSUser)
    ```


### WorkOSOrganizationMembership

Represents a user's membership in an organization. This links users to organizations and defines their roles within the organization.

| Field | Description |
|-------|-------------|
| id | The identifier, which can be referenced in API endpoints |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| user_id | The ID of the user |
| organization_id | The ID of the organization |
| status | The status of the membership (e.g., active, pending) |
| role_id | The ID of the role assigned to the user |
| created_at | The RFC 3339 datetime of when the membership was created |
| updated_at | The RFC 3339 datetime of when the membership was last updated |

#### Relationships
- `OrganizationMembership` belongs to an `Environment`
    ```
    (WorkOSEnvironment)-[:RESOURCE]->(WorkOSOrganizationMembership)
    ```
- `User` is member of `OrganizationMembership`
    ```
    (WorkOSUser)-[:MEMBER_OF]->(WorkOSOrganizationMembership)
    ```
- `OrganizationMembership` is in `Organization`
    ```
    (WorkOSOrganizationMembership)-[:IN]->(WorkOSOrganization)
    ```
- `OrganizationMembership` has `Role`
    ```
    (WorkOSOrganizationMembership)-[:WITH_ROLE]->(WorkOSRole)
    ```


### WorkOSRole

Represents a role within an organization. Roles define permissions and access levels for users.

| Field | Description |
|-------|-------------|
| id | The identifier, which can be referenced in API endpoints |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| slug | A unique slug identifier for the role |
| name | The name of the role |
| description | A description of the role |
| type | The type of the role (e.g., environment, organization) |
| organization_id | The ID of the organization this role belongs to |
| created_at | The RFC 3339 datetime of when the role was created |
| updated_at | The RFC 3339 datetime of when the role was last updated |

#### Relationships
- `Role` belongs to an `Environment`
    ```
    (WorkOSEnvironment)-[:RESOURCE]->(WorkOSRole)
    ```
- `Organization` has `Role`
    ```
    (WorkOSOrganization)-[:HAS]->(WorkOSRole)
    ```


### WorkOSInvitation

Represents an invitation to join an organization. Invitations are sent to users to join specific organizations.

| Field | Description |
|-------|-------------|
| id | The identifier, which can be referenced in API endpoints |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| email | The email address of the invited user |
| state | The state of the invitation (e.g., pending, accepted, expired) |
| organization_id | The ID of the organization the user is invited to |
| inviter_user_id | The ID of the user who sent the invitation |
| expires_at | The RFC 3339 datetime when the invitation expires |
| created_at | The RFC 3339 datetime of when the invitation was created |
| updated_at | The RFC 3339 datetime of when the invitation was last updated |
| accepted_at | The RFC 3339 datetime of when the invitation was accepted |
| revoked_at | The RFC 3339 datetime of when the invitation was revoked |

#### Relationships
- `Invitation` belongs to an `Environment`
    ```
    (WorkOSEnvironment)-[:RESOURCE]->(WorkOSInvitation)
    ```
- `Invitation` is for `Organization`
    ```
    (WorkOSInvitation)-[:FOR_ORGANIZATION]->(WorkOSOrganization)
    ```
- `Invitation` invites `User`
    ```
    (WorkOSInvitation)-[:INVITES]->(WorkOSUser)
    ```
- `Invitation` was created by `User`
    ```
    (WorkOSInvitation)-[:INVITED_BY]->(WorkOSUser)
    ```


### WorkOSDirectory

Represents a directory sync connection. Directories are used to sync users and groups from external identity providers (e.g., Google Workspace, Okta, Azure AD).

| Field | Description |
|-------|-------------|
| id | The identifier, which can be referenced in API endpoints |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| name | The name of the directory |
| domain | The domain associated with the directory |
| state | The state of the directory (e.g., linked, unlinked) |
| type | The type of identity provider (e.g., gsuite, okta, azure) |
| organization_id | The ID of the organization this directory belongs to |
| created_at | The RFC 3339 datetime of when the directory was created |
| updated_at | The RFC 3339 datetime of when the directory was last updated |

#### Relationships
- `Directory` belongs to an `Environment`
    ```
    (WorkOSEnvironment)-[:RESOURCE]->(WorkOSDirectory)
    ```
- `Directory` belongs to `Organization`
    ```
    (WorkOSDirectory)-[:BELONGS_TO]->(WorkOSOrganization)
    ```
- `Directory` has `DirectoryUser`
    ```
    (WorkOSDirectory)-[:HAS]->(WorkOSDirectoryUser)
    ```
- `Directory` has `DirectoryGroup`
    ```
    (WorkOSDirectory)-[:HAS]->(WorkOSDirectoryGroup)
    ```


### WorkOSDirectoryUser

Represents a user synced from an external directory. These are different from WorkOSUser objects and represent users from identity providers.

**Ontology Labels**: `UserAccount`

| Field | Description |
|-------|-------------|
| id | The identifier, which can be referenced in API endpoints |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| idp_id | The identifier from the identity provider |
| directory_id | The ID of the directory this user belongs to |
| organization_id | The ID of the organization this user belongs to |
| first_name | The first name of the user |
| last_name | The last name of the user |
| email | The email address of the user |
| state | The state of the directory user (e.g., active, inactive) |
| created_at | The RFC 3339 datetime of when the directory user was created |
| updated_at | The RFC 3339 datetime of when the directory user was last updated |
| custom_attributes | Custom attributes from the identity provider |
| raw_attributes | Raw attributes from the identity provider |
| roles | JSON list of directory role slugs assigned to the user by the IdP |

#### Relationships
- `DirectoryUser` belongs to an `Environment`
    ```
    (WorkOSEnvironment)-[:RESOURCE]->(WorkOSDirectoryUser)
    ```
- `Directory` has `DirectoryUser`
    ```
    (WorkOSDirectory)-[:HAS]->(WorkOSDirectoryUser)
    ```
- `DirectoryUser` belongs to `Organization`
    ```
    (WorkOSDirectoryUser)-[:BELONGS_TO]->(WorkOSOrganization)
    ```
- `DirectoryUser` is member of `DirectoryGroup`
    ```
    (WorkOSDirectoryUser)-[:MEMBER_OF]->(WorkOSDirectoryGroup)
    ```


### WorkOSDirectoryGroup

Represents a group synced from an external directory. Groups contain directory users and represent organizational units from identity providers.

| Field | Description |
|-------|-------------|
| id | The identifier, which can be referenced in API endpoints |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| idp_id | The identifier from the identity provider |
| name | The name of the group |
| created_at | The RFC 3339 datetime of when the directory group was created |
| updated_at | The RFC 3339 datetime of when the directory group was last updated |
| raw_attributes | Raw attributes from the identity provider |

#### Relationships
- `DirectoryGroup` belongs to an `Environment`
    ```
    (WorkOSEnvironment)-[:RESOURCE]->(WorkOSDirectoryGroup)
    ```
- `Directory` has `DirectoryGroup`
    ```
    (WorkOSDirectory)-[:HAS]->(WorkOSDirectoryGroup)
    ```
- `DirectoryGroup` belongs to `Organization`
    ```
    (WorkOSDirectoryGroup)-[:BELONGS_TO]->(WorkOSOrganization)
    ```


### WorkOSOrganizationDomain

Represents a domain verified for an organization. Domains are used to verify ownership of email domains and can be used for automatic user assignment.

| Field | Description |
|-------|-------------|
| id | The identifier, which can be referenced in API endpoints |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| domain | The domain name (e.g., example.com) |
| organization_id | The ID of the organization this domain belongs to |
| state | The verification state of the domain (e.g., verified, pending) |
| verification_strategy | The strategy used to verify the domain |
| verification_token | The token used for domain verification |

#### Relationships
- `OrganizationDomain` belongs to an `Environment`
    ```
    (WorkOSEnvironment)-[:RESOURCE]->(WorkOSOrganizationDomain)
    ```
- `OrganizationDomain` is domain of `Organization`
    ```
    (WorkOSOrganizationDomain)-[:DOMAIN_OF]->(WorkOSOrganization)
    ```


### WorkOSAPIKey

Represents an API key used for programmatic access to WorkOS resources.

> **Ontology Mapping**: This node has the extra label `APIKey` to enable cross-platform queries for API keys across different systems (e.g., OpenAIApiKey, ScalewayAPIKey).

| Field | Description |
|-------|-------------|
| id | The identifier, which can be referenced in API endpoints |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| name | The name of the API key |
| obfuscated_value | The obfuscated/partial API key value |
| permissions | The permissions granted to this API key |
| created_at | The RFC 3339 datetime of when the API key was created |
| updated_at | The RFC 3339 datetime of when the API key was last updated |
| last_used_at | The RFC 3339 datetime of when the API key was last used |

#### Relationships
- `APIKey` belongs to an `Environment`
    ```
    (WorkOSEnvironment)-[:RESOURCE]->(WorkOSAPIKey)
    ```
- `Organization` owns `APIKey`
    ```
    (WorkOSOrganization)-[:OWNS]->(WorkOSAPIKey)
    ```


### WorkOSApplication

Represents a Connect application integrated with WorkOS. These can be OAuth applications or Machine-to-Machine (M2M) applications.

> **Ontology Mapping**: This node has the extra label `ThirdPartyApp` to enable cross-platform queries for OAuth/SAML applications across different systems (e.g., OktaApplication, KeycloakClient).


| Field | Description |
|-------|-------------|
| id | The identifier, which can be referenced in API endpoints |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| client_id | The OAuth client ID for the application |
| name | The name of the application |
| description | A description of the application |
| application_type | The type of application. Set to `m2m` for Machine-to-Machine applications; null for OAuth applications. |
| scopes | The OAuth scopes granted to this application |
| created_at | The RFC 3339 datetime of when the application was created |
| updated_at | The RFC 3339 datetime of when the application was last updated |

#### Relationships
- `Application` belongs to an `Environment`
    ```
    (WorkOSEnvironment)-[:RESOURCE]->(WorkOSApplication)
    ```
- `Application` belongs to `Organization` (M2M applications only)
    ```
    (WorkOSApplication)-[:BELONGS_TO]->(WorkOSOrganization)
    ```
- `Application` has client secrets
    ```
    (WorkOSApplication)-[:HAS_SECRET]->(WorkOSApplicationClientSecret)
    ```


### WorkOSApplicationClientSecret

Represents a client secret (credential) attached to a WorkOS Connect application, typically used by M2M applications to authenticate and obtain access tokens. The plaintext secret value is never exposed by the WorkOS API after creation; only a `secret_hint` (the last few characters) is available.

> **Ontology Mapping**: This node has the extra label `APIKey` to enable cross-platform queries for long-lived authentication credentials across different systems.


| Field | Description |
|-------|-------------|
| id | The identifier of the client secret |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| secret_hint | The last few characters of the secret value (for identification) |
| last_used_at | Timestamp of the last time this secret was used, or null if never used |
| created_at | The RFC 3339 datetime of when the secret was created |
| updated_at | The RFC 3339 datetime of when the secret was last updated |

#### Relationships
- `ApplicationClientSecret` belongs to an `Environment`
    ```
    (WorkOSEnvironment)-[:RESOURCE]->(WorkOSApplicationClientSecret)
    ```
- `ApplicationClientSecret` is owned by an `Application`
    ```
    (WorkOSApplication)-[:HAS_SECRET]->(WorkOSApplicationClientSecret)
    ```
