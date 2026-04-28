## AIBOM Schema

The AIBOM module uses a mostly source-faithful model with one pragmatic simplification:

- `AIBOMSource` is the primary scanned-target node. It combines the report-envelope metadata and the source entry because real AIBOM usage here is effectively one meaningful source per image.
- `AIBOMComponent` represents one detected component occurrence within a source.
- `AIBOMComponent.logical_id` provides a stable callsite-style fingerprint so equivalent components can be grouped across repeated rebuilds and image churn.
- `AIBOMWorkflow` represents workflow context emitted by the scanner.
- `AIBOMComponent` nodes are linked directly for common AIBOM relationships such as `USES_TOOL`, `USES_MODEL`, and `USES_MEMORY`.

### AIBOMSource

Representation of one scanned target within the AIBOM output. In practice this is the node you traverse from `Image` to reach the rest of the AI inventory.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Stable hash of matched image identity + scanner metadata + source key |
| **image_uri** | Image URI provided in the report envelope |
| manifest_digests | Canonical image digests resolved from `image_uri`, when available |
| image_matched | Whether `image_uri` resolved to an `Image` node already in the graph |
| scan_scope | Scanner input scope |
| report_location | Local file path or `s3://` object URI used for ingestion |
| scanner_name | Scanner name |
| scanner_version | Scanner version |
| analyzer_version | Analyzer version reported by AIBOM |
| analysis_status | Top-level analysis status if present |
| report_total_sources | Number of sources in the report |
| report_total_components | Total detected components across all sources in the report |
| report_total_workflows | Total workflows across all sources in the report |
| report_total_relationships | Total component relationships across all sources in the report |
| report_category_summary_json | JSON summary of category counts across the report |
| **source_key** | Native source key emitted by AIBOM |
| source_status | Source status (for example `completed` or `failed`) |
| source_kind | Optional source kind emitted by AIBOM |
| total_components | Total components found in this source |
| total_workflows | Total workflows found in this source |
| total_relationships | Total component relationships found in this source |
| category_summary_json | JSON summary of component category counts for this source |

#### Relationships

- A source points to the canonical image it scanned when that image exists in the graph.

    ```
    (:AIBOMSource)-[:SCANNED_IMAGE]->(:Image)
    ```

- A source contains component occurrences.

    ```
    (:AIBOMSource)-[:HAS_COMPONENT]->(:AIBOMComponent)
    ```

- A source contains workflow entries.

    ```
    (:AIBOMSource)-[:HAS_WORKFLOW]->(:AIBOMWorkflow)
    ```

- An analysis job creates a shortcut edge from a source to every container running the scanned image. This is computed by joining `SCANNED_IMAGE` with `RESOLVED_IMAGE` on the same concrete `:Image` node, inheriting the architecture matching and determinism guards from `resolved_image_analysis.json`.

    ```
    (:AIBOMSource)-[:RUNS_ON]->(:Container)
    ```

### AIBOMComponent

Representation of one detected AI component occurrence within a source.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Stable hash of source id + component occurrence identity fields |
| logical_id | Stable hash of category + symbol + stable callsite fields used to group equivalent components across images |
| name | Detected symbol name |
| **category** | Category emitted by AIBOM (for example `agent`, `model`, `tool`, `memory`, `prompt`, `other`) |
| instance_id | AIBOM component instance identifier |
| assigned_target | Optional assigned target from the scanner |
| file_path | File path reported by the scanner |
| line_number | Line number reported by the scanner |
| model_name | Optional model name emitted by the source; queryable metadata rather than part of the stable logical fingerprint |
| framework | Optional framework emitted by the source |
| label | Optional source-defined label or custom concept emitted by AIBOM; queryable metadata rather than part of the stable logical fingerprint |
| manifest_digests | Digests of the canonical images used for graph linking |

`AIBOMComponent` also gets conditional category labels for discoverability:

- `AIAgent` when `category = "agent"`
- `AIModel` when `category = "model"`
- `AITool` when `category = "tool"`
- `AIMemory` when `category = "memory"`
- `AIEmbedding` when `category = "embedding"`
- `AIPrompt` when `category = "prompt"`

#### Relationships

- A component occurrence is detected in the canonical image resolved for the report.

    ```
    (:AIBOMComponent)-[:DETECTED_IN]->(:Image)
    ```

- A component may participate in one or more workflow contexts.

    ```
    (:AIBOMComponent)-[:IN_WORKFLOW]->(:AIBOMWorkflow)
    ```

- Common agentic relationships are materialized directly between components.

    ```
    (:AIAgent)-[:USES_TOOL]->(:AITool)
    (:AIAgent)-[:USES_MODEL]->(:AIModel)
    (:AIAgent)-[:USES_MEMORY]->(:AIMemory)
    (:AIAgent)-[:USES_PROMPT]->(:AIPrompt)
    ```

- `USES_LLM` from the source payload is normalized to `USES_MODEL` in the graph so model relationships query consistently with other AI modules.

#### Identity notes

- `id` stays occurrence-oriented so relationships such as `DETECTED_IN`, `IN_WORKFLOW`, and `USES_*` remain correct for a specific scanned artifact.
- `logical_id` is the cross-image grouping key. It is derived from stable callsite-like fields: category, name, file path, assigned target, and framework.
- `label` is intentionally excluded from `logical_id` because it is source-defined metadata that may change when catalogs or classifiers change even if the underlying code callsite does not.
- `model_name` is intentionally excluded from `logical_id` because security engineers usually want an agent to remain the same logical agent when its model dependency changes; that change should show up in `USES_MODEL` relationships rather than redefining the agent identity.
- When multiple components within a single source share the same higher-level fingerprint, Cartography adds deterministic fallback fields (`instance_id` and `line_number`) to avoid collapsing distinct detections.

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

### Relationship ingestion

- Source `relationships` are used to create direct component-to-component edges for the built-in AIBOM relationship types currently supported by Cartography.
- Unsupported custom relationship types are counted on `AIBOMSource.total_relationships` but are not materialized as graph edges.

### Linking constraints

- If the envelope `image_uri` contains a digest (`repo@sha256:...`), the digest is extracted directly and verified against any node carrying the `:Image` ontology label. No graph traversal is needed.
- For tag-based URIs (`repo:tag`), AIBOM resolves digests via `ECRRepositoryImage` → `ECRImage` as a provider-specific fallback. Single-platform images are returned directly. For manifest lists, the resolver traverses `CONTAINS_IMAGE` to return all child single-platform image digests.
- A source without an image match is still preserved as `AIBOMSource {image_matched: false}` for coverage and troubleshooting, but it will not create `AIBOMSource -> Image` links, and `AIBOMComponent` nodes are not materialized until a canonical digest is resolved.

### Example queries

Find production images that contain agent components:

```cypher
MATCH (source:AIBOMSource)-[:SCANNED_IMAGE]->(img:Image)
MATCH (source)-[:HAS_COMPONENT]->(component:AIBOMComponent)
WHERE component.category = 'agent'
RETURN source.image_uri, img._ont_digest, collect(component.name)
```

Find agent-to-tool relationships:

```cypher
MATCH (img:Image)<-[:DETECTED_IN]-(agent:AIAgent)-[:USES_TOOL]->(tool:AITool)
RETURN img._ont_digest, agent.name, tool.name
```

Group equivalent agents across rebuilds:

```cypher
MATCH (component:AIAgent)
RETURN component.logical_id, collect(DISTINCT component.name), count(*) AS detections
ORDER BY detections DESC
```
