## Airbyte Schema

```mermaid
graph LR
O(Organization) -- RESOURCE --> W(Workspace)
O -- RESOURCE --> U(User)
O -- RESOURCE --> S(Source)
O -- RESOURCE --> D(Destination)
O -- RESOURCE --> T(Tag)
O -- RESOURCE --> C(Connection)
O -- RESOURCE --> Str(Stream)
W -- CONTAINS --> S
W -- CONTAINS --> D
W -- CONTAINS --> T
W -- CONTAINS --> C
C -- SYNC_FROM --> S
C -- SYNC_TO --> D
C -- TAGGED --> T
C -- HAS --> Str
U -- ADMIN_OF --> O
U -- ADMIN_OF --> W
U -- MEMBER_OF --> W
```

### AirbyteOrganization

Provides details of a single organization for a user.

| Field | Description |
|-------|-------------|
| id | The organization UUID |
| name | The name of the organization |
| email | Contact email for the organization  |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |


#### Relationships
- `Workspace`, `User`, `Source`, `Destination`, `Tag`, `Connection`, `Stream` belong to an `Organization`.
    ```
    (:AirbyteOrganization)-[:RESOURCE]->(
        :AirbyteWorkspace,
        :AirbyteUser,
        :AirbyteSource,
        :AirbyteDestination,
        :AirbyteTag,
        :AirbyteConnection,
        :AirbyteStream
    )
    ```
- `User` is admin of an `Organization`
    ```
    (:AirbyteUser)-[:ADMIN_OF]->(:AirbyteOrganization)
    ```


### AirbyteWorkspace

Provides details of a single workspace.

| Field | Description |
|-------|-------------|
| id | UUID of the workspace |
| name | Name of the workspace |
| data_residency | Localization of the data (us, eu) |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |


#### Relationships
- `Workspace` belong to an `Organization`
    ```
    (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteWorkspace)
    ```
- `Workspace` contains `Source`, `Destination`, `Tag`, `Connection`
    ```
    (:AirbyteWorkspace)-[:CONTAINS]->(
        :AirbyteSource,
        :AirbyteDestination,
        :AirbyteTag,
        :AirbyteConnection
    )
    ```
- `User` is admin of an `Workspace`
    ```
    (:AirbyteUser)-[:ADMIN_OF]->(:AirbyteWorkspace)
    ```
- `User` is member of an `Workspace`
    ```
    (:AirbyteUser)-[:MEMBER_OF]->(:AirbyteWorkspace)
    ```


### AirbyteUser

Provides details of a single user in an organization.

| Field | Description |
|-------|-------------|
| id | Internal Airbyte user ID |
| name | Name of the user |
| email | Email of the user |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |

#### Relationships
- `User` belong to an `Organization`
    ```
    (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteUser)
    ```
- `User` is admin of an `Organization`
    ```
    (:AirbyteUser)-[:ADMIN_OF]->(:AirbyteOrganization)
    ```
- `User` is admin of an `Workspace`
    ```
    (:AirbyteUser)-[:ADMIN_OF]->(:AirbyteWorkspace)
    ```
- `User` is member of an `Workspace`
    ```
    (:AirbyteUser)-[:ADMIN_OF]->(:AirbyteWorkspace)
    ```


### AirbyteSource

Provides details of a single source.

| Field | Description |
|-------|-------------|
| id | UUID of the source |
| name | Name of the source |
| type | Type of the source (eg. postgres, s3) |
| config_host | Host of the source |
| config_port | Port of the source |
| config_name | Name of the source (can be database name, bucket name, container name ...) |
| config_region | Name of the regions (can be the AWS region) |
| config_endpoint | Endpoint for the source |
| config_account | Account of the source (can be AWSAccount, AzureAccount)
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |


### Relationships

- `Source` belong to an `Organization`
    ```
    (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteSource)
    ```
- `Workspace` contains `Source`
    ```
    (:AirbyteWorkspace)-[:CONTAINS]->(:AirbyteSource)
    ```
- `Connection` synchronizes data from a `Source`
    ```
    (:AirbyteConnection)-[:SYNC_FROM]->(:AirbyteSource)
    ```


### AirbyteDestination

Provides details of a single destination.

| Field | Description |
|-------|-------------|
| id | UUID of the destination |
| name | Name of the destination |
| type | Type of the destination (eg. postgres, s3) |
| config_host | Host of the destination |
| config_port | Port of the destination |
| config_name | Name of the destination (can be database name, bucket name, container name ...) |
| config_region | Name of the regions (can be the AWS region) |
| config_endpoint | Endpoint for the destination |
| config_account | Account of the destination (can be AWSAccount, AzureAccount)
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |

### Relationships

- `Destination` belong to an `Organization`
    ```
    (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteDestination)
    ```
- `Workspace` contains `Destination`
    ```
    (:AirbyteWorkspace)-[:CONTAINS]->(:AirbyteDestination)
    ```
- `Connection` synchronizes data to a `Destination`
    ```
    (:AirbyteConnection)-[:SYNC_TO]->(:AirbyteDestination)
    ```

### AirbyteTag

Provides details of a single tag.

| Field | Description |
|-------|-------------|
| id | UUID of the tag |
| name | Name of the tag |
| color | hex color of the tag |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |

### Relationships
- `Tag` belong to an `Organization`
    ```
    (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteTag)
    ```
- `Workspace` contains `Tag`
    ```
    (:AirbyteWorkspace)-[:CONTAINS]->(:AirbyteTag)
    ```
- `Connection` is tagged with a `Tag`
    ```
    (:AirbyteConnection)-[:TAGGED]->(:AirbyteTag)
    ```

### AirbyteConnection

Provides details of a single connection.

| Field | Description |
|-------|-------------|
| id | UUID of the connection |
| name | name of the connection
| namespace_format |  |
| prefix | Prefix text to each stream name in the destination |
| status | Status of the connection |
| data_residency | Localization of the connection (eg. us, eu) |
| namespace_definition | Define the location where the data will be stored in the destination |
| non_breaking_schema_updates_behavior | Set how Airbyte handles syncs when it detects a non-breaking schema change in the source |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |


#### Relationships
- `Connection` belong to an `Organization`
    ```
    (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteConnection)
    ```
- `Workspace` contains `Connection`
    ```
    (:AirbyteWorkspace)-[:CONTAINS]->(:AirbyteConnection)
    ```
- `Connection` is tagged with a `Tag`
    ```
    (:AirbyteConnection)-[:TAGGED]->(:AirbyteTag)
    ```
- `Connection` synchronizes data from a `Source`
    ```
    (:AirbyteConnection)-[:SYNC_FROM]->(:AirbyteSource)
    ```
- `Connection` synchronizes data to a `Destination`
    ```
    (:AirbyteConnection)-[:SYNC_TO]->(:AirbyteDestination)
    ```
- `Connection` has `Stream`
    ```
    (:AirbyteConnection)-[:HAS]->(:AirbyteStream)
    ```

### AirbyteStream

Represents a single stream of a connection.

| Field | Description |
|-------|-------------|
| id | Crafted ID for the stream (`connectionUUID_streamName`) |
| name | name of the stream |
| sync_mode | sync method for the stream |
| cursor_field | name of the column that is used as a cursor |
| primary_key | primary key for the stream |
| include_files | flag for including raw files for blob sync |
| selected_fields | fields to sync for the stream |
| mappers | custom mappers for the stream |
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |

#### Relationships
- `Stream` belong to an `Organization`
    ```
    (:AirbyteOrganization)-[:RESOURCE]->(:AirbyteStream)
    ```
- `Connection` has `Stream`
    ```
    (:AirbyteConnection)-[:HAS]->(:AirbyteStream)
    ```
