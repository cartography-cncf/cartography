## AIBOM Schema

The AIBOM module now ingests raw AIBOM `1.0.0rc4` reports directly and loads
them into a source/component graph model that is anchored either to a concrete
ontology `:Image` node (for container-image scans) or to a code repository
(`:GitHubRepository` / `:GitLabProject`) for source-code scans.

- `AIBOMSource` is the primary scanned-target node.
- `AIBOMComponent` represents one detected component occurrence within that
  source.
- `AIBOMComponent.logical_id` provides a stable fingerprint that can be used to
  group equivalent components across repeated rebuilds and image churn.
- Workflow-like context in `1.0.0rc4` is preserved through component evidence
  and metadata fields rather than first-class workflow nodes.
- Component-to-component AIBOM edges are loaded directly from the report's
  `relationships` array as standard component-owned relationships between
  `AIBOMComponent` nodes.

### AIBOMSource

Representation of one scanned source in the AIBOM output. In practice this is
the node you traverse from `Image` to reach the rest of the AI inventory for a
scanned artifact.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Stable hash of the source key |
| **image_uri** | Source image URI derived from `source_name` when present, otherwise the `source_key` |
| manifest_digests | Concrete image digests extracted from the source key |
| image_matched | Whether the ingested source carried a digest-qualified anchor; accepted reports are pre-validated against concrete `:Image` nodes before load |
| report_location | Local file path or object-store URI used for ingestion |
| run_id | Report run identifier |
| analyzer_version | AIBOM analyzer version |
| analysis_status | Top-level report status |
| report_schema_version | AIBOM report schema version |
| report_started_at | Report start timestamp |
| report_completed_at | Report completion timestamp |
| report_output_format | Output format reported by AIBOM |
| llm_model | LLM model used during analysis when present |
| sources_requested | Number of requested sources in the report |
| sources_analyzed | Number of analyzed sources in the report |
| sources_with_errors | Number of errored sources in the report |
| error_count | Total report error count |
| prompt_tokens | Top-level prompt token count |
| completion_tokens | Top-level completion token count |
| total_tokens | Top-level total token count |
| report_total_sources | Top-level summary total source count |
| report_total_components | Top-level summary total component count |
| report_total_relationships | Top-level summary total relationship count |
| pending_agent_review | Top-level summary pending review count |
| test_only_components | Top-level summary test-only component count |
| report_component_types | Sorted list of top-level component categories |
| report_component_type_counts | Counts matching `report_component_types` |
| risk_score | Top-level risk score |
| risk_severity | Top-level risk severity |
| **source_key** | Native source key emitted by AIBOM |
| source_name | Source name emitted by AIBOM, falling back to `source_key` when absent |
| source_path | Extracted filesystem path used during scanning |
| source_status | Source status (for example `completed`) |
| source_kind | Source kind (for example `container`) |
| total_components | Source-level component total |
| total_relationships | Source-level relationship total |
| assets_discovered | Source-level discovered asset count |
| last_generated_at | Source generation timestamp |
| source_elapsed_s | Source-level elapsed time |
| source_prompt_tokens | Source-level prompt token count |
| source_completion_tokens | Source-level completion token count |
| source_total_tokens | Source-level total token count |
| source_component_types | Sorted list of component categories present in this source |
| source_component_type_counts | Counts matching `source_component_types` |

#### Relationships

- A source points to the concrete image it scanned.

    ```
    (:AIBOMSource)-[:SCANNED_IMAGE]->(:Image)
    ```

- A source built from a code-repository scan points to the repository it
  scanned. Only the matching repository type present in the graph is linked.

    ```
    (:AIBOMSource)-[:SCANNED_REPOSITORY]->(:GitHubRepository)
    (:AIBOMSource)-[:SCANNED_REPOSITORY]->(:GitLabProject)
    ```

- A source contains component occurrences.

    ```
    (:AIBOMSource)-[:HAS_COMPONENT]->(:AIBOMComponent)
    ```

- An analysis job creates a shortcut edge from a source to every container
  running the scanned image. This is computed by joining `SCANNED_IMAGE` with
  `RESOLVED_IMAGE` on the same concrete `:Image` node.

    ```
    (:AIBOMSource)-[:RUNS_ON]->(:Container)
    ```

### AIBOMComponent

Representation of one detected AI component occurrence within a source.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Stable hash of source key + component occurrence identity fields |
| logical_id | Stable cross-source fingerprint for equivalent components |
| name | Detected component name |
| **category** | Normalized component category used for grouping and filtering |
| component_type | AIBOM component type from the report |
| instance_id | AIBOM component instance identifier |
| file_path | File path reported for the component |
| line_number | Line number reported for the component |
| model_name | Model name when the component identifies a concrete model |
| embedding_model | Embedding model metadata when present |
| framework | Framework or provider hint emitted by AIBOM |
| detection_source | Detection origin such as `code_analysis`, `agentic`, or `config_file` |
| confidence | Final component confidence |
| heuristic_confidence | Heuristic confidence from the report |
| agentic_confidence | Agentic confidence from the report |
| needs_agentic | Whether the component required agentic review |
| agentic_hint | Agentic hint text |
| description | Component description |
| text | Raw component text/value when present |
| transport | Transport metadata when present |
| config_source | Configuration source metadata when present |
| storage_uri | Storage URI when present |
| dataset_source | Dataset source metadata when present |
| skill_format | Skill format metadata when present |
| sdk_version | SDK/package version metadata when present |
| kb_concept | Knowledge-base concept metadata when present |
| kb_label | Knowledge-base label metadata when present |
| component_primary_evidence | Primary evidence file path chosen from `decision_annotation.evidence_locations` |
| component_primary_evidence_start_line | Start line of the primary evidence location |
| component_primary_evidence_end_line | End line of the primary evidence location |
| decision | `decision_annotation.decision` for the component |
| decision_justification | `decision_annotation.justification` for the component |
| metadata_json | Serialized component metadata preserved until category-specific remodel work lands |
| manifest_digests | Concrete image digests used to link the component to `:Image` |

#### Relationships

- A component occurrence is detected in the concrete image resolved for the
  source.

    ```
    (:AIBOMComponent)-[:DETECTED_IN]->(:Image)
    ```

- For source-code scans, a component occurrence is detected in the code
  repository resolved for the source. Only the matching repository type present
  in the graph is linked: the resolved URI is matched against
  `GitHubRepository.url` and `GitLabProject.web_url`.

    ```
    (:AIBOMComponent)-[:DETECTED_IN]->(:GitHubRepository)
    (:AIBOMComponent)-[:DETECTED_IN]->(:GitLabProject)
    ```

- Report-defined component-to-component relationships are loaded between
  `AIBOMComponent` nodes when both endpoints resolve successfully within the
  same scanned source. During transform, the source component payload owns the
  target component id arrays that drive these one-to-many relationships. The
  current implementation supports:

    ```
    (:AIBOMComponent)-[:USES_MODEL]->(:AIBOMComponent)
    (:AIBOMComponent)-[:USES_TOOL]->(:AIBOMComponent)
    (:AIBOMComponent)-[:EXPOSES_TOOL]->(:AIBOMComponent)
    (:AIBOMComponent)-[:CUSTOM]->(:AIBOMComponent)
    ```

#### Identity notes

- `id` is occurrence-oriented and includes source context, so the same-looking
  component in different scanned sources will not collide.
- `logical_id` is the cross-source grouping key. It is derived from stable
  callsite-style fields such as component type, name, file path, framework,
  model name, storage URI, and skill format.
- `metadata_json` intentionally preserves category-specific metadata until the
  follow-up data-model redesign decides which component categories should become
  their own first-class node types.

### Linking constraints

- Each AIBOM source key is anchored to an existing target node before the
  report is ingested:
    - Digest-qualified source keys such as `repo@sha256:...` must resolve to a
      concrete `(:Image {_ont_digest: ...})` node.
    - Any other source key is treated as a code-repository URI and must resolve
      to an existing `(:GitHubRepository {url: ...})` or
      `(:GitLabProject {web_url: ...})` node.
- `aibom_analysis.sources` must be non-empty. Empty source maps are treated as
  malformed input and fail AIBOM sync.
- `:ImageManifestList` and `:ImageTag` are not valid primary anchors for this
  ingestion flow.
- If any source key fails to resolve to its expected target node, Cartography
  raises an error and fails the AIBOM sync run rather than partially loading
  data.

### Example queries

Find production images that contain agent components:

```cypher
MATCH (source:AIBOMSource)-[:SCANNED_IMAGE]->(img:Image)
MATCH (source)-[:HAS_COMPONENT]->(component:AIBOMComponent)
WHERE component.category = 'agent'
RETURN source.image_uri, img._ont_digest, collect(component.name)
```

Find the components detected in a concrete image:

```cypher
MATCH (img:Image)<-[:DETECTED_IN]-(component:AIBOMComponent)
RETURN img._ont_digest, component.category, component.name
ORDER BY component.category, component.name
```

Group equivalent components across rebuilds:

```cypher
MATCH (component:AIBOMComponent)
RETURN component.logical_id, collect(DISTINCT component.name), count(*) AS detections
ORDER BY detections DESC
```
