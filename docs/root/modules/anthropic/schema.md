## Anthropic Schema

```mermaid
graph LR
O(Organization) -- RESOURCE --> W(Workspace)
O -- RESOURCE --> U(User)
O -- RESOURCE --> K(ApiKey)
W -- CONTAINS --> K
U -- OWNS --> K
U -- MEMBER_OF --> W
U -- ADMIN_OF --> W
```


### AnthropicOrganization

Represents an Anthropic Organization

| Field | Description |
|-------|-------------|
| id | The identifier, which can be referenced in API endpoints |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |

#### Relationships
- Other resources belongs to an `Organization`
    ```
    (AnthropicOrganization)-[:RESOURCE]->(
        :AnthropicApiKey,
        :AnthropicUser,
        :AnthropicWorkspace)
    ```


### AnthropicUser

Represents an individual `user` within an organization.

| Field | Description |
|-------|-------------|
| id | The identifier, which can be referenced in API endpoints |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| name | The name of the user |
| email | The email address of the user |
| role | `admin` or `user` |
| added_at | The RFC 3339 datetime of when the user was added. |

#### Relationships
- `User` belongs to an `Organization`
    ```
    (AnthropicOrganization)-[:RESOURCE]->(AnthropicApiKey)
    ```
- `API Key` is owned by a `User`
    ```
    (:AnthropicUser)-[:OWNS]->(:AnthropicApiKey)
    ```
- `User` are member of a `Workspace`
    ```
    (:AnthropicUser)-[:MEMBER_OF]->(:AnthropicWorkspace)
    ```
- `User` are admin of a `Workspace`
    ```
    (:AnthropicUser)-[:ADMIN_OF]->(:AnthropicWorkspace)
    ```


### AnthropicWorkspace

Represents an individual workspace.

| Field | Description |
|-------|-------------|
| id | The identifier, which can be referenced in API endpoints |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| name | The name of the project. This appears in reporting. |
| created_at | The RFC 3339 datetime of when the project was created. |
| archived_at | The RFC 3339 datetime of when the project was archived or `null`. |
| display_color | Hex color code representing the Workspace in the Anthropic Console. |

#### Relationships
- `Workspace` belongs to an `Organization`
    ```
    (:AnthropicOrganization)-[:RESOURCE]->(:AnthropicWorkpace)
    ```
- `Workspace` contains `ApiKey`
    ```
    (:AnthropicWorkspace)-[:CONTAINS]->(:AnthropicApiKey)
    ```
- `User` are member of a `Workpace`
    ```
    (:AnthropicUser)-[:MEMBER_OF]->(:AnthropicWorkpace)
    ```
- `User` are admin of a `Workpace`
    ```
    (:AnthropicUser)-[:ADMIN_OF]->(:AnthropicWorkpace)
    ```


### AnthropicApiKey

Represents an individual API key in a project.

| Field | Description |
|-------|-------------|
| id | The identifier, which can be referenced in API endpoints |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| name | The name of the API key |
| status | Status of the API key. Available options: active, inactive, archived  |
| created_at | The RFC 3339 datetime of when the API key was created |
| last_used_at | The RFC 3339 datetime of when the API key was last used. |

#### Relationships
- `Apikey` belongs to an `Organization`
    ```
    (:AnthropicOrganization)-[:RESOURCE]->(:AnthropicApiKey)
    ```
- `APIKey` is owned by a `User`
    ```
    (:AnthropicUser)-[:OWNS]->(:AnthropicApiKey)
    ```
- `Workspace` contains `ApiKey`
    ```
    (:AnthropicWorkspace)-[:CONTAINS]->(:AnthropicApiKey)
    ```
