## AIBOM Schema

### AIBOMComponent

Representation of one AI component detection from an AIBOM report.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Stable hash of manifest digest + component identity fields |
| name | Detected symbol name (for example `langchain.agents.create_agent`) |
| **category** | Category emitted by AIBOM (for example `agent`, `tool`, `other`) |
| instance_id | AIBOM component instance identifier |
| assigned_target | AIBOM assigned target value |
| file_path | File path reported by the scanner |
| line_number | Line number reported by the scanner |
| **source_image_uri** | Source image URI associated with the report |
| scanner_name | Scanner name |
| scanner_version | Scanner version |
| scan_scope | Scanner input scope |
| **manifest_digest** | Digest of the canonical ECRImage used for graph linking |

#### Relationships

- An AIBOMComponent is detected in the canonical ECR image resolved for the source image URI.

    ```
    (:AIBOMComponent)-[:DETECTED_IN]->(:ECRImage)
    ```

- An AIBOMComponent participates in an AIBOMWorkflow.

    ```
    (AIBOMComponent)-[:IN_WORKFLOW]->(AIBOMWorkflow)
    ```

### AIBOMWorkflow

Representation of a workflow/function context emitted by AIBOM and referenced by components.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Stable hash of manifest digest + workflow id |
| workflow_id | Original workflow id from AIBOM output |
| function | Workflow function name |
| file_path | File path for the workflow |
| line | Line number for the workflow |
| distance | Workflow distance reported by AIBOM |

### Linking constraints

- If the envelope `image_uri` contains a digest (`repo@sha256:...`), the digest is extracted directly and verified against `ECRImage` nodes. No graph traversal is needed.
- For tag-based URIs (`repo:tag`), AIBOM resolves the digest via `ECRRepositoryImage` → `ECRImage`, preferring `type = "manifest_list"` over `type = "image"`.
- AIBOM detections are linked to only one `ECRImage` per source image URI.
