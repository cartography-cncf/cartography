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
| **manifest_digest** | Manifest-list digest used for graph linking |

#### Relationships

- An AIBOMComponent is detected in a manifest-list ECR image.

    ```
    (AIBOMComponent)-[:DETECTED_IN]->(ECRImage::ImageManifestList)
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

- AIBOM ingestion links only to `ECRImage` nodes with `type = "manifest_list"`.
- Platform-specific `ECRImage` nodes (`type = "image"`) are not link targets for AIBOM detections.
