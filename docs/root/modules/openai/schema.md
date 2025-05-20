## OpenAI Schema



### AdminApiKey

Represents an individual Admin API key in an org.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| object | The object type, which is always `organization.admin_api_key` |
| id | The identifier, which can be referenced in API endpoints |
| name | The name of the API key |
| redacted_value | The redacted value of the API key |
| value | The value of the API key. Only shown on create. |
| created_at | The Unix timestamp (in seconds) of when the API key was created |
| last_used_at | The Unix timestamp (in seconds) of when the API key was last used |
| owner_type | Always `user` |
| owner_object | The object type, which is always organization.user |
| owner_id | The identifier, which can be referenced in API endpoints |
| owner_name | The name of the user |
| owner_created_at | The Unix timestamp (in seconds) of when the user was created |
| owner_role | Always `owner` |



### User

Represents an individual `user` within an organization.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| object | The object type, which is always `organization.user` |
| id | The identifier, which can be referenced in API endpoints |
| name | The name of the user |
| email | The email address of the user |
| role | `owner` or `reader` |
| added_at | The Unix timestamp (in seconds) of when the user was added. |



### Project

Represents an individual project.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The identifier, which can be referenced in API endpoints |
| object | The object type, which is always `organization.project` |
| name | The name of the project. This appears in reporting. |
| created_at | The Unix timestamp (in seconds) of when the project was created. |
| archived_at | The Unix timestamp (in seconds) of when the project was archived or `null`. |
| status | `active` or `archived` |

#### Relationships
- Some node types belong to an `OpenAIProject`.
    ```
    (:OpenAIProject)<-[:RESOURCE]-(
        :OpenAIServiceAccount,
        :OpenAIApiKey,
    )
    ```


### ProjectServiceAccount

Represents an individual service account in a project.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| object | The object type, which is always `organization.project.service_account` |
| id | The identifier, which can be referenced in API endpoints |
| name | The name of the service account |
| role | `owner` or `member` |
| created_at | The Unix timestamp (in seconds) of when the service account was created |

#### Relationships
- `OpenAIServiceAccount` belongs to a `OpenAIProject`
    ```
    (:OpenAIServiceAccount)-[:RESOURCE]->(:OpenAIProject)
    ```


### ProjectApiKey

Represents an individual API key in a project.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| object | The object type, which is always `organization.project.api_key` |
| redacted_value | The redacted value of the API key |
| name | The name of the API key |
| created_at | The Unix timestamp (in seconds) of when the API key was created |
| last_used_at | The Unix timestamp (in seconds) of when the API key was last used. |
| id | The identifier, which can be referenced in API endpoints |
| owner_type | `user` or `service_account` |
| owner_user |  |
| owner_service_account |  |

#### Relationships
- `OpenAIApiKey` belongs to a `OpenAIProject`
    ```
    (:OpenAIApiKey)-[:RESOURCE]->(:OpenAIProject)
    ```


### VectorStore

A vector store is a collection of processed files can be used by the `file_search` tool.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The identifier, which can be referenced in API endpoints. |
| object | The object type, which is always `vector_store`. |
| created_at | The Unix timestamp (in seconds) for when the vector store was created. |
| name | The name of the vector store. |
| usage_bytes | The total number of bytes used by the files in the vector store. |
| file_counts_in_progress | The number of files that are currently being processed. |
| file_counts_completed | The number of files that have been successfully processed. |
| file_counts_failed | The number of files that have failed to process. |
| file_counts_cancelled | The number of files that were cancelled. |
| file_counts_total | The total number of files. |
| status | The status of the vector store, which can be either `expired`, `in_progress`, or `completed`. A status of `completed` indicates that the vector store is ready for use. |
| expires_at | The Unix timestamp (in seconds) for when the vector store will expire. |
| last_active_at | The Unix timestamp (in seconds) for when the vector store was last active. |
| expires_after_id | ID of the VectorStoreExpirationAfter entity |
| metadata_id | ID of the Metadata entity |



### Assistant

Represents an `assistant` that can call the model and use tools.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The identifier, which can be referenced in API endpoints. |
| object | The object type, which is always `assistant`. |
| created_at | The Unix timestamp (in seconds) for when the assistant was created. |
| name | The name of the assistant. The maximum length is 256 characters. |
| description | The description of the assistant. The maximum length is 512 characters. |
| model | ID of the model to use. You can use the [List models](/docs/api-reference/models/list) API to see all of your available models, or see our [Model overview](/docs/models) for descriptions of them. |
| instructions | The system instructions that the assistant uses. The maximum length is 256,000 characters. |
| temperature | What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic. |
| top_p | An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.<br/><br/>We generally recommend altering this or temperature but not both. |
| metadata_id | ID of the Metadata entity |
| response_format_id | ID of the AssistantsApiResponseFormatOption entity |

