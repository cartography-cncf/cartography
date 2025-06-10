## Okta Schema

### OktaOrganization

Representation of an [Okta Organization](https://developer.okta.com/docs/concepts/okta-organizations/).


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

| Field | Description |
|-------|--------------|
| id | user id  |
| first_name | user first name  |
| last_name | user last name  |
| login | user usernmae used to login (usually email) |
| email | user email |
| second_email | user secondary email |
| mobile_phone | user mobile phone |
| created | date and time of creation |
| activated | date and time of activation |
| status_changed | date and time of the last state change |
| last_login | date and time of last login |
| okta_last_updated | date and time of last user property changes |
| password_changed | date and time of last password change |
| transition_to_status | date and time of last state transition change |
| firstseen| Timestamp of when a sync job first discovered this node  |
| lastupdated |  Timestamp of the last time the node was updated |

#### Relationships

 - An OktaOrganization contains OktaUsers
    ```
    (OktaUser)<-[RESOURCE]->(OktaOrganization)
    ```
 - OktaUsers are assigned OktaApplication

    ```
    (OktaUser)-[APPLICATION]->(OktaApplication)
    ```
 - OktaUser is an identity for a Human

    ```
    (OktaUser)<-[IDENTITY_OKTA]-(Human)
    ```
 - An OktaUser can be a member of an OktaGroup
     ```
    (OktaUser)-[MEMBER_OF_OKTA_GROUP]->(OktaGroup)
    ```
 - An OktaUser can be a member of an OktaAdministrationRole
     ```
    (OktaUser)-[MEMBER_OF_OKTA_ROLE]->(OktaAdministrationRole)
    ```
 - OktaUsers can have authentication factors
     ```
    (OktaUser)-[FACTOR]->(OktaUserFactor)
    ```

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

### Reply Uri

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
