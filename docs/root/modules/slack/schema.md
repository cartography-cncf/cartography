## Slack Schema

```mermaid
graph LR
ST(SlackTeam) -- RESOURCE --> SU(SlackUser)
ST -- RESOURCE --> SC(SlackChannel)
ST -- RESOURCE --> SG(SlackGroup)
SU -- CREATED --> SC
SU -- MEMBER_OF --> SC
SU -- MEMBER_OF --> SG
SU -- CREATED --> SG
SG -- MEMBER_OF --> SC
```

### SlackTeam

Representation of a Slack Workspace.

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for organizational tenants across different systems (e.g., GitHubOrganization, AWSAccount, SpaceliftAccount).

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Slack ID |
| name | Slack workspace name (eg. Lyft OSS) |
| domain | Slack workspace slug (eg. lyftoss) |
| url | Slack workspace full url (eg. https://lyftoss.slack.com) |
| is_verified | Flag for verified Slack workspace (boolean) |
| email_domain | Slack workspace email domain (eg. lyft.com) |

#### Relationships

- A SlackTeam contains SlackUser

    ```
    (SlackTeam)-[RESOURCE]->(SlackUser)
    ```

- A SlackTeam contains SlackChannels

    ```
    (SlackTeam)-[RESOURCE]->(SlackChannel)
    ```

- A SlackTeam contains SlackGroup

    ```
    (SlackTeam)-[RESOURCE]->(SlackGroup)
    ```

### SlackUser

Representation of a single [User in Slack](https://api.slack.com/types/user).

> **Ontology Mapping**: This node has the extra label `UserAccount` to enable cross-platform queries for user accounts across different systems (e.g., OktaUser, AWSSSOUser, EntraUser).

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Slack ID |
| name | Slack username (eg. john.doe) |
| real_name | User full name (eg. John Doe) |
| display_name | User displayed name (eg. John D.) |
| first_name | User first name (eg. John) |
| last_name | User last name (eg. Doe) |
| profile_title | User job function (eg. Cybersecurity Manager) |
| profile_phone | User phone number (eg. +33 6 11 22 33 44) |
| email | User email (eg. john.doe@evilcorp.com) |
| deleted | Flag for deleted users (boolean) |
| is_admin | Flag for admin users (boolean) |
| is_owner | Flag for Slack Workspace owners (boolean) |
| is_restricted | Flag for restricted users, aka guests (boolean) |
| is_ultra_restricted | Flag for ultra restricted users, aka guests (boolean) |
| is_bot | Flag for bot user accounts (boolean) |
| is_app_user | Flag for application user accounts (boolean) |
| is_email_confirmed | Flag for user with confirmed email (boolean) |
| has_mfa | Flag for users with multi-factor authentication enabled (boolean) |
| team | Slack team ID |

#### Relationships

- A SlackTeam contains SlackUser

    ```
    (SlackTeam)-[RESOURCE]->(SlackUser)
    ```

- A SlackChannel is created by a SlackUser

    ```
    (SlackUser)-[:CREATED]->(SlackChannel)
    ```

- A SlackUser is a member of a SlackChannel

    ```
    (SlackUser)-[:MEMBER_OF]->(:SlackChannel)
    ```

- A SlackUser is member of a SlackGroup

    ```
    (SlackUser)-[:MEMBER_OF]->(SlackGroup)
    ```

- A SlackGroup is created by a SlackUser

    ```
    (SlackUser)-[CREATED]->(SlackGroup)
    ```


### SlackChannel

Representation of a single [Channel in Slack](https://api.slack.com/types/channel).

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Slack ID |
| name | Slack channel name (eg. concern-it) |
| is_private | Flag for private channels (boolean) |
| created | Slack channel creation timestamp |
| is_archived | Flag for archived channels (boolean) |
| is_general | Flag for users default channels (boolean) |
| is_shared | Flag for channels shared with other workspaces |
| is_org_shared | Flag for channel shared with other workspaces in same organization |
| num_members | Number of members in the channel |
| topic | Slack channel topic |
| purpose | Slack channel purpose |

#### Relationships

- A SlackTeam contains SlackChannel

    ```
    (SlackTeam)-[RESOURCE]->(SlackChannel)
    ```

- A SlackChannel is created by a SlackUser

    ```
    (SlackUser)-[:CREATED]->(SlackChannel)
    ```

- A SlackUser is a member of a SlackChannel

    ```
    (SlackUser)-[:MEMBER_OF]->(:SlackChannel)
    ```

- A SlackGroup is member of a SlackChannel

    ```
    (SlackChannel)<-[MEMBER_OF]-(SlackGroup)
    ```


### SlackGroup

Representation of a single [Group in Slack](https://api.slack.com/types/usergroup).

| Field | Description |
|-------|--------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Slack ID |
| name | Slack group name (eg. Security Team) |
| description | Slack group description |
| is_subteam | Flag for sub-groups  |
| handle | Slack handle (eg. security-team) |
| is_external | Flag for external groups |
| date_create | Slack group creation timestamp |
| date_update | Slack group last update timestamp |
| date_delete | Slack group deletion timestamp |
| updated_by | User ID who has performed last group update |
| user_count | Number of members |
| channel_count | Number of channels where group is member |

#### Relationships

- A SlackTeam contains SlackGroup

    ```
    (SlackTeam)-[RESOURCE]->(SlackGroup)
    ```

- A SlackUser is member of a SlackGroup

    ```
    (SlackUser)-[MEMBER_OF]->(SlackGroup)
    ```

- A SlackGroup is member of a SlackChannel

    ```
    (SlackChannel)<-[MEMBER_OF]-(SlackGroup)
    ```

- A SlackGroup is created by a SlackUser

    ```
    (SlackUser)-[CREATED]->(SlackGroup)
    ```
