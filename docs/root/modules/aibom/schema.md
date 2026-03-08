## AIBOM Schema

The AIBOM module uses a source-faithful model:

- `AIBOMScan` represents one ingested report envelope for one image.
- `AIBOMSource` represents one source entry inside the report.
- `AIBOMComponent` represents one detected component occurrence within a source.
- `AIBOMWorkflow` represents workflow context emitted by the scanner.
- `AIBOMRelationship` preserves source-defined component relationships such as `USES_TOOL` or `USES_LLM`.

### AIBOMScan

Representation of one ingested AIBOM report for one image URI.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Stable hash of the matched image identity and scan metadata |
| **image_uri** | Image URI provided in the report envelope |
| manifest_digest | Canonical `ECRImage.digest` resolved from `image_uri`, when available |
| image_matched | Whether `image_uri` resolved to an `ECRImage` already in the graph |
| scan_scope | Scanner input scope |
| report_location | Local file path or `s3://` object URI used for ingestion |
| scanner_name | Scanner name |
| scanner_version | Scanner version |
| analyzer_version | Analyzer version reported by AIBOM |
| analysis_status | Top-level analysis status if present |
| total_sources | Number of sources in the report |
| total_components | Total detected components across all sources |
| total_workflows | Total workflows across all sources |
| total_relationships | Total component relationships across all sources |
| category_summary_json | JSON summary of category counts across the report |

#### Relationships

- An `AIBOMScan` points to the canonical image it scanned when that image exists in the graph.

    ```
    (:AIBOMScan)-[:SCANNED_IMAGE]->(:ECRImage)
    ```

- An `AIBOMScan` contains one or more `AIBOMSource` entries.

    ```
    (:AIBOMScan)-[:HAS_SOURCE]->(:AIBOMSource)
    ```

### AIBOMSource

Representation of one source entry within the scanner output.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Stable hash of scan id + source key |
| **source_key** | Native source key emitted by AIBOM |
| source_status | Source status (for example `completed` or `failed`) |
| source_kind | Optional source kind emitted by AIBOM |
| total_components | Total components found in this source |
| total_workflows | Total workflows found in this source |
| total_relationships | Total component relationships found in this source |
| category_summary_json | JSON summary of component category counts for this source |

#### Relationships

- A source contains component occurrences.

    ```
    (:AIBOMSource)-[:HAS_COMPONENT]->(:AIBOMComponent)
    ```

- A source contains workflow entries.

    ```
    (:AIBOMSource)-[:HAS_WORKFLOW]->(:AIBOMWorkflow)
    ```

- A source contains relationship entries between components.

    ```
    (:AIBOMSource)-[:HAS_RELATIONSHIP]->(:AIBOMRelationship)
    ```

### AIBOMComponent

Representation of one detected AI component occurrence within a source.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Stable hash of source id + component identity fields |
| name | Detected symbol name |
| **category** | Category emitted by AIBOM (for example `agent`, `model`, `tool`, `memory`, `prompt`, `other`) |
| instance_id | AIBOM component instance identifier |
| assigned_target | Optional assigned target from the scanner |
| file_path | File path reported by the scanner |
| line_number | Line number reported by the scanner |
| model_name | Optional model name emitted by the source |
| framework | Optional framework emitted by the source |
| label | Optional label emitted by the source |
| metadata_json | Optional JSON-encoded metadata emitted by the source |
| manifest_digest | Digest of the canonical `ECRImage` used for graph linking |

#### Relationships

- A component occurrence is detected in the canonical image resolved for the report.

    ```
    (:AIBOMComponent)-[:DETECTED_IN]->(:ECRImage)
    ```

- A component may participate in one or more workflow contexts.

    ```
    (:AIBOMComponent)-[:IN_WORKFLOW]->(:AIBOMWorkflow)
    ```

### AIBOMWorkflow

Representation of a workflow/function context emitted by AIBOM.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Stable hash of source id + workflow id |
| workflow_id | Original workflow id from AIBOM output |
| function | Workflow function name |
| file_path | File path for the workflow |
| line | Line number for the workflow |
| distance | Workflow distance reported by AIBOM |

### AIBOMRelationship

Representation of one source-defined relationship between two component occurrences.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Stable hash of source id + relationship type + source component + target component |
| **relationship_type** | Native relationship type emitted by AIBOM (for example `USES_TOOL`, `USES_LLM`) |
| raw_source_instance_id | Raw source instance id from the scanner payload |
| raw_target_instance_id | Raw target instance id from the scanner payload |
| raw_source_name | Raw source component name from the scanner payload |
| raw_target_name | Raw target component name from the scanner payload |
| raw_source_category | Raw source component category from the scanner payload |
| raw_target_category | Raw target component category from the scanner payload |

#### Relationships

- An `AIBOMRelationship` points back to its source component.

    ```
    (:AIBOMComponent)-[:FROM_COMPONENT]->(:AIBOMRelationship)
    ```

- An `AIBOMRelationship` points to its target component.

    ```
    (:AIBOMRelationship)-[:TO_COMPONENT]->(:AIBOMComponent)
    ```

### Linking constraints

- If the envelope `image_uri` contains a digest (`repo@sha256:...`), the digest is extracted directly and verified against `ECRImage` nodes. No graph traversal is needed.
- For tag-based URIs (`repo:tag`), AIBOM resolves the digest via `ECRRepositoryImage` → `ECRImage`, preferring `type = "manifest_list"` over `type = "image"`.
- A scan without an image match is still preserved as `AIBOMScan {image_matched: false}` for coverage and troubleshooting, but it will not create `AIBOMComponent -> ECRImage` links.

### Example queries

Find production images that contain agent components:

```cypher
MATCH (scan:AIBOMScan)-[:SCANNED_IMAGE]->(img:ECRImage)
MATCH (scan)-[:HAS_SOURCE]->(:AIBOMSource)-[:HAS_COMPONENT]->(component:AIBOMComponent)
WHERE component.category = 'agent'
RETURN scan.image_uri, img.digest, collect(component.name)
```

Find agent-to-tool relationships:

```cypher
MATCH (source:AIBOMSource)-[:HAS_RELATIONSHIP]->(rel:AIBOMRelationship {relationship_type: 'USES_TOOL'})
MATCH (agent:AIBOMComponent)-[:FROM_COMPONENT]->(rel)-[:TO_COMPONENT]->(tool:AIBOMComponent)
RETURN source.source_key, agent.name, tool.name
```
