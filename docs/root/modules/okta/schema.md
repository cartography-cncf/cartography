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
- An OktaOrganization has OktaAdministrationRoles

    ```
    (OktaOrganization)-[RESOURCE]->(OktaAdministrationRole)
    ```

### OktaUser

Representation of an [Okta User](https://developer.okta.com/docs/reference/api/users/#user-object).

> **Ontology Mapping**: This node has the extra label `UserAccount` to enable cross-platform queries for user accounts across different systems (e.g., AWSSSOUser, EntraUser, GitHubUser).

| Field | Description |
|-------|--------------|
| **id** | Unique Okta user ID (e.g., "00u1a2b3c4d5e6f7g8h9") |
| **email** | User's primary email address (also used for Human node linking) |
| first_name | User's first name |
| last_name | User's last name |
| login | Username used for login (typically an email address) |
| second_email | User's secondary email address, if configured |
| mobile_phone | User's mobile phone number, if configured |
| created | ISO 8601 timestamp when the user was created in Okta |
| activated | ISO 8601 timestamp when the user was activated |
| status_changed | ISO 8601 timestamp of the last status change |
| last_login | ISO 8601 timestamp of the user's last login |
| okta_last_updated | ISO 8601 timestamp when user properties were last modified in Okta |
| password_changed | ISO 8601 timestamp when the user's password was last changed |
| transition_to_status | ISO 8601 timestamp of the last status transition |
| firstseen | Timestamp when Cartography first discovered this node |
| lastupdated | Timestamp when Cartography last updated this node |

#### Relationships

- **OktaOrganization contains OktaUsers**: Every OktaUser belongs to an OktaOrganization
    ```cypher
    (:OktaOrganization)-[:RESOURCE]->(:OktaUser)
    ```

- **OktaUser is an identity for a Human**: Links Okta identities to Human entities (matched by email)
    ```cypher
    (:Human)-[:IDENTITY_OKTA]->(:OktaUser)
    ```
    This relationship allows tracking the same person across multiple identity systems. The Human node is automatically created based on the OktaUser's email address.

- **OktaUsers are assigned OktaApplications**: Tracks which applications a user has access to
    ```cypher
    (:OktaUser)-[:APPLICATION]->(:OktaApplication)
    ```

- **OktaUser can be a member of OktaGroups**: Group membership for access control
    ```cypher
    (:OktaUser)-[:MEMBER_OF_OKTA_GROUP]->(:OktaGroup)
    ```

- **OktaUser can be a member of OktaAdministrationRoles**: Administrative role assignments
    ```cypher
    (:OktaUser)-[:MEMBER_OF_OKTA_ROLE]->(:OktaAdministrationRole)
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

| Field | Description |
|-------|--------------|
| id | application id  |
| name | group name |
| description | group description |
| sam_account_name | windows SAM account name mapped
| dn | group dn |
| windows_domain_qualified_name | windows domain name |
| external_id | group foreign id |
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
 - An OktaGroup can be a member of an OktaAdministrationRole
     ```
    (OktaGroup)-[MEMBER_OF_OKTA_ROLE]->(OktaAdministrationRole)
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
    (ReplyUri)-[REPLYURI]->(OktaApplication)
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

### OktaAdministrationRole

Representation of an [Okta Administration Role](https://developer.okta.com/docs/reference/api/roles/#role-object).

| Field | Description |
|-------|--------------|
| id | role id mapped to the type |
| type | role type |
| label | role label |
| firstseen| Timestamp of when a sync job first discovered this node |
| lastupdated |  Timestamp of the last time the node was updated |

#### Relationships

 - OktaUsers can be members of OktaAdministrationRoles
     ```
    (OktaUser)-[MEMBER_OF_OKTA_ROLE]->(OktaAdministrationRole)
    ```
 - An OktaGroup can be a member of an OktaAdministrationRolee
     ```
    (OktaGroup)-[MEMBER_OF_OKTA_ROLE]->(OktaAdministrationRole)
    ```
- An OktaOrganization contains OktaAdministrationRoles

    ```
    (OktaOrganization)-[RESOURCE]->(OktaAdministrationRole)
    ```

### ReplyUri

Representation of [Okta Application ReplyUri](https://developer.okta.com/docs/reference/api/apps/).

| Field | Description |
|-------|--------------|
| id | uri the app can send the reply to |
| uri | uri the app can send the reply to |
| valid | is the DNS of the reply uri valid. Invalid replyuris can lead to oath phishing |
| firstseen| Timestamp of when a sync job first discovered this node |
| lastupdated |  Timestamp of the last time the node was updated |

#### Relationships

 - OktaApplications have ReplyUris

    ```
    (ReplyUri)-[REPLYURI]->(OktaApplication)
    ```
