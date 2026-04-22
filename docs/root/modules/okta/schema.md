## Okta Schema

> **Note on Schema Introspection**: OktaUser and other Okta nodes do not have formal `CartographyNodeSchema` models and use legacy Cypher query-based ingestion. This means schema introspection APIs may return empty results for Okta nodes. Refer to this documentation for complete schema information including node properties and relationships.

Okta integrates with AWS through SAML federation, allowing Okta users to access AWS resources. The complete relationship path is:

```cypher
(:OktaUser)-[:CAN_ASSUME_IDENTITY]->(:AWSSSOUser)-[:ASSUMED_ROLE_WITH_SAML]->(:AWSRole)
```

**How it works:**
1. **OktaUser to AWSSSOUser**: When Okta is configured as a SAML identity provider for AWS Identity Center (formerly AWS SSO), OktaUsers can assume AWSSSOUser identities. The link is established by matching the `AWSSSOUser.external_id` with the `OktaUser.id`.
2. **AWSSSOUser to AWSRole**: When users actually assume roles through AWS Identity Center, CloudTrail management events record these assumptions as `ASSUMED_ROLE_WITH_SAML` relationships.


### OktaOrganization

Representation of an [Okta Organization](https://developer.okta.com/docs/concepts/okta-organizations/).

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for organizational tenants across different systems (e.g., AWSAccount, AzureTenant, GCPOrganization).

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The name of the Okta Organization, e.g. "lyft" |
| name | The name of the Okta Organization, e.g. "lyft"

#### Relationships

- An OktaOrganization contains OktaUsers

    ```
    (OktaOrganization)-[RESOURCE]->(OktaUser)
    ```

- An OktaOrganization contains OktaGroups.

    ```
    (OktaOrganization)-[RESOURCE]->(OktaGroup)
    ```
- An OktaOrganization contains OktaApplications

    ```
    (OktaOrganization)-[RESOURCE]->(OktaApplication)
    ```
- An OktaOrganization has OktaTrustedOrigins

    ```
    (OktaOrganization)-[RESOURCE]->(OktaTrustedOrigin)
    ```

### OktaUser

Representation of an [Okta User](https://developer.okta.com/docs/reference/api/users/#user-object).

> **Ontology Mapping**: This node has the extra label `UserAccount` to enable cross-platform queries for user accounts across different systems (e.g., AWSSSOUser, EntraUser, GitHubUser).

| Field | Description |
|-------|--------------|
| **id** | Unique Okta user ID (e.g., "00u1a2b3c4d5e6f7g8h9") |
| **email** | User's primary email address (also used for Human node linking) |
| login | Username used for login (typically an email address) |
| second_email | User's secondary email address, if configured |
| status | Okta user lifecycle status (e.g. `ACTIVE`, `SUSPENDED`) |
| type | OktaUserType id the user belongs to |
| created | ISO 8601 timestamp when the user was created in Okta |
| activated | ISO 8601 timestamp when the user was activated |
| status_changed | ISO 8601 timestamp of the last status change |
| last_login | ISO 8601 timestamp of the user's last login |
| okta_last_updated | ISO 8601 timestamp when user properties were last modified in Okta |
| password_changed | ISO 8601 timestamp when the user's password was last changed |
| transition_to_status | ISO 8601 timestamp of the last status transition |
| first_name, last_name, middle_name | Given name components |
| honorific_prefix, honorific_suffix | Name prefix / suffix |
| display_name, nick_name | Display-friendly names |
| profile_url | Profile URL |
| locale, preferred_language, timezone | Locale / i18n preferences |
| user_type | Free-form user type label from the Okta profile |
| title, department, division, organization | Employment metadata |
| cost_center, employee_number | Finance / HR identifiers |
| manager, manager_id | Manager name and Okta id |
| mobile_phone, primary_phone | Phone numbers |
| street_address, city, state, zip_code, country_code, postal_address | Address fields |
| custom_attributes | JSON-serialized tenant-specific profile attributes (Okta `additional_properties`). Null when absent. |
| firstseen | Timestamp when Cartography first discovered this node |
| lastupdated | Timestamp when Cartography last updated this node |

#### Relationships

- **OktaOrganization contains OktaUsers**: Every OktaUser belongs to an OktaOrganization
    ```cypher
    (:OktaOrganization)-[:RESOURCE]->(:OktaUser)
    ```

- **OktaUsers are assigned OktaApplications**: Tracks which applications a user has access to
    ```cypher
    (:OktaUser)-[:APPLICATION]->(:OktaApplication)
    ```

- **OktaUser can be a member of OktaGroups**: Group membership for access control
    ```cypher
    (:OktaUser)-[:MEMBER_OF_OKTA_GROUP]->(:OktaGroup)
    ```

- **OktaUsers can have authentication factors**: Multi-factor authentication methods (SMS, TOTP, WebAuthn, etc.)
    ```cypher
    (:OktaUser)-[:FACTOR]->(:OktaUserFactor)
    ```

- **OktaUsers can assume AWS SSO identities via SAML federation**: Links to AWS Identity Center users
    ```cypher
    (:OktaUser)-[:CAN_ASSUME_IDENTITY]->(:AWSSSOUser)
    ```
    This relationship is established when Okta is configured as a SAML identity provider for AWS Identity Center. The link is matched by `AWSSSOUser.external_id == OktaUser.id`.

    Using the generic UserAccount label:
    ```cypher
    (:UserAccount)-[:CAN_ASSUME_IDENTITY]->(:AWSSSOUser)
    ```
    See the [Cross-Platform Integration](#cross-platform-integration-okta-to-aws) section above for the complete Okta → AWS access path.

### OktaGroup

Representation of an [Okta Group](https://developer.okta.com/docs/reference/api/groups/#group-object).

> **Ontology Mapping**: This node has the extra label `UserGroup` to enable cross-platform queries for user groups across different systems (e.g., AWSGroup, EntraGroup, GoogleWorkspaceGroup).

| Field | Description |
|-------|--------------|
| id | application id  |
| **name** | group name |
| description | group description |
| sam_account_name | windows SAM account name mapped
| dn | group dn |
| windows_domain_qualified_name | windows domain name |
| external_id | group foreign id |
| created | When the group was created in Okta |
| last_membership_updated | When group membership was last updated |
| last_updated | When the group was last updated |
| object_class | Okta object class (e.g. `okta:user_group`) |
| group_type | Group type reported by Okta (e.g. `OKTA_GROUP`, `APP_GROUP`) |
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |

#### Relationships

 - OktaOrganizations contain OktaGroups
    ```
    (OktaGroup)<-[RESOURCE]->(OktaOrganizations)
    ```
 - OktaApplications can be assigned to OktaGroups

    ```
    (OktaGroup)-[APPLICATION]->(OktaApplication)
    ```
 - An OktaUser can be a member of an OktaGroup
     ```
    (OktaUser)-[MEMBER_OF_OKTA_GROUP]->(OktaGroup)
    ```
 - An OktaGroup can have an OktaGroupRole assigned to it
     ```
    (OktaGroup)-[HAS_ROLE]->(OktaGroupRole)
    ```
- Members of an Okta group can assume associated AWS roles if Okta SAML is configured with AWS.
    ```
    (AWSRole)-[ALLOWED_BY]->(OktaGroup)
    ```

### OktaApplication

Representation of an [Okta Application](https://developer.okta.com/docs/reference/api/apps/#application-object).

> **Ontology Mapping**: This node has the extra label `ThirdPartyApp` to enable cross-platform queries for OAuth/SAML applications across different systems (e.g., EntraApplication, KeycloakClient).

| Field | Description |
|-------|--------------|
| id | application id |
| name | application name |
| label | application label |
| created | application creation date |
| okta_last_updated | date and time of last application property changes |
| status | application status |
| activated | application activation state |
| features | application features |
| sign_on_mode | application signon mode |
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |

#### Relationships

  - OktaApplication is a resource of an OktaOrganization
    ```
    (OktaApplication)<-[RESOURCE]->(OktaOrganization)
    ```
 - OktaGroups can be assigned OktaApplications

    ```
    (OktaGroup)-[APPLICATION]->(OktaApplication)
    ```
 - OktaUsers are assigned OktaApplications

    ```
    (OktaUser)-[APPLICATION]->(OktaApplication)
    ```
- OktaApplications have ReplyUris

    ```
    (OktaApplication)-[REPLYURI]->(ReplyUri)
    ```

### OktaUserFactor

Representation of Okta User authentication [Factors](https://developer.okta.com/docs/reference/api/factors/#factor-object).

| Field | Description |
|-------|--------------|
| id | factor id |
| factor_type | factor type |
| provider | factor provider |
| status | factor status |
| created | factor creation date and time |
| okta_last_updated | date and time of last property changes |
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |

#### Relationships

 - OktaUsers can have authentication Factors
     ```
    (OktaUser)-[FACTOR]->(OktaUserFactor)
    ```

### OktaTrustedOrigin

Representation of an [Okta Trusted Origin](https://developer.okta.com/docs/reference/api/trusted-origins/#trusted-origin-object) for login/logout or recovery operations.

| Field | Description |
|-------|--------------|
| id | trusted origin id |
| name | name |
| scopes | array of scope |
| status | status |
| created | date & time of creation in okta |
| create_by | id of user who created the trusted origin |
| okta_last_updated | date and time of last property changes |
| okta_last_updated_by | id of user who last updated the trusted origin |
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |

#### Relationships

- An OktaOrganization has OktaTrustedOrigins.

    ```
    (OktaOrganization)-[RESOURCE]->(OktaTrustedOrigin)
    ```

### OktaUserRole

Representation of an administrative [Okta Role](https://developer.okta.com/docs/reference/api/roles/) assigned directly to an OktaUser.

| Field | Description |
|-------|--------------|
| **id** | Okta role assignment id |
| assignment_type | `USER` or `GROUP` |
| created | When the role assignment was created |
| description | Role description |
| label | Human-readable role label |
| name | Role name |
| role_type | Role type (e.g. `SUPER_ADMIN`, `ORG_ADMIN`) |
| status | Role assignment status |
| last_updated | When the role assignment was last updated |
| firstseen | Timestamp when Cartography first discovered this node |
| lastupdated | Timestamp when Cartography last updated this node |

#### Relationships

- An OktaOrganization contains OktaUserRoles
    ```
    (OktaOrganization)-[RESOURCE]->(OktaUserRole)
    ```
- An OktaUser can have OktaUserRoles
    ```
    (OktaUser)-[HAS_ROLE]->(OktaUserRole)
    ```

### OktaUserType

Representation of an [Okta User Type](https://developer.okta.com/docs/reference/api/user-types/).

> **SDK limitation**: The Okta Python SDK's `UserType` model only exposes the
> `id` field; richer metadata returned by the API (name, display_name,
> description, timestamps, …) is discarded before it reaches us. The node is
> therefore kept minimal and mostly used as a join target for
> `(OktaUser)-[:HAS_TYPE]->(OktaUserType)`. Tracked upstream at
> [okta/okta-sdk-python#535](https://github.com/okta/okta-sdk-python/issues/535).

| Field | Description |
|-------|--------------|
| **id** | User type id |
| firstseen | Timestamp when Cartography first discovered this node |
| lastupdated | Timestamp when Cartography last updated this node |

#### Relationships

- An OktaOrganization contains OktaUserTypes
    ```
    (OktaOrganization)-[RESOURCE]->(OktaUserType)
    ```
- An OktaUser is of a given OktaUserType
    ```
    (OktaUser)-[HAS_TYPE]->(OktaUserType)
    ```

### OktaGroupRole

Representation of an administrative [Okta Role](https://developer.okta.com/docs/reference/api/roles/) assigned to an OktaGroup.

| Field | Description |
|-------|--------------|
| **id** | Okta role assignment id |
| assignment_type | `USER` or `GROUP` |
| created | When the role assignment was created |
| description | Role description |
| label | Human-readable role label |
| name | Role name |
| role_type | Role type (e.g. `SUPER_ADMIN`, `ORG_ADMIN`) |
| status | Role assignment status |
| last_updated | When the role assignment was last updated |
| firstseen | Timestamp when Cartography first discovered this node |
| lastupdated | Timestamp when Cartography last updated this node |

#### Relationships

- An OktaOrganization contains OktaGroupRoles
    ```
    (OktaOrganization)-[RESOURCE]->(OktaGroupRole)
    ```
- An OktaGroup can have OktaGroupRoles
    ```
    (OktaGroup)-[HAS_ROLE]->(OktaGroupRole)
    ```

### OktaGroupRule

Representation of an [Okta Group Rule](https://developer.okta.com/docs/reference/api/groups/#group-rule-object).

| Field | Description |
|-------|--------------|
| **id** | Group rule id |
| name | Group rule name |
| status | Rule status (`ACTIVE`, `INACTIVE`) |
| created | Creation timestamp |
| last_updated | Last update timestamp |
| condition_type | One of `expression`, `group_membership`, `complex` |
| conditions | Rule condition payload (expression string or JSON) |
| expression_type | Expression language type when `condition_type=expression` |
| inclusions | User ids included by the rule, if any |
| exclusions | User ids excluded by the rule, if any |
| assigned_groups | Group ids the rule assigns users to |
| firstseen | Timestamp when Cartography first discovered this node |
| lastupdated | Timestamp when Cartography last updated this node |

#### Relationships

- An OktaOrganization contains OktaGroupRules
    ```
    (OktaOrganization)-[RESOURCE]->(OktaGroupRule)
    ```
- An OktaGroupRule assigns users to one or more OktaGroups
    ```
    (OktaGroupRule)-[ASSIGNED_BY_GROUP_RULE]->(OktaGroup)
    ```

### OktaAuthenticator

Representation of an [Okta Authenticator](https://developer.okta.com/docs/reference/api/authenticators-admin/).

| Field | Description |
|-------|--------------|
| **id** | Authenticator id |
| name | Authenticator name |
| key | Authenticator key (e.g. `okta_password`, `webauthn`) |
| authenticator_type | Authenticator type |
| status | Authenticator status |
| created | Creation timestamp |
| last_updated | Last update timestamp |
| provider_type | Provider type when applicable |
| provider_host_name | Provider host name |
| provider_auth_port | Provider auth port |
| provider_instance_id | Provider instance id |
| provider_integration_key | Provider integration key |
| provider_secret_key | Provider secret key |
| provider_shared_secret | Provider shared secret |
| provider_user_name_template | Provider user name template |
| provider_configuration | Full provider configuration as JSON |
| settings_allowed_for | Contexts the authenticator is allowed for |
| settings_token_lifetime_minutes | Token lifetime in minutes |
| settings_compliance | Compliance settings |
| settings_channel_binding | Channel binding style |
| settings_user_verification | User verification setting |
| settings_app_instance_id | Bound app instance id |
| settings | Full settings payload as JSON |
| firstseen | Timestamp when Cartography first discovered this node |
| lastupdated | Timestamp when Cartography last updated this node |

#### Relationships

- An OktaOrganization has OktaAuthenticators
    ```
    (OktaOrganization)-[RESOURCE]->(OktaAuthenticator)
    ```

### ReplyUri

Representation of [Okta Application ReplyUri](https://developer.okta.com/docs/reference/api/apps/).

| Field | Description |
|-------|--------------|
| id | uri the app can send the reply to |
| uri | uri the app can send the reply to |
| firstseen| Timestamp of when a sync job first discovered this node |
| lastupdated |  Timestamp of the last time the node was updated |

#### Relationships

 - OktaApplications have ReplyUris

    ```
    (OktaApplication)-[REPLYURI]->(ReplyUri)
    ```
