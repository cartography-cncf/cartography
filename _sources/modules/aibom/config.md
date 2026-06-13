## AIBOM Configuration

The AIBOM module ingests pre-generated [Cisco AI BOM](https://github.com/cisco-ai-defense/aibom) JSON reports and maps them onto container images already present in Cartography.

Cartography does not run the scanner in this module. It only ingests JSON artifacts from local disk or supported object stores.

### Why this module exists

Traditional image inventory tells you what packages and vulnerabilities exist in a container. It does not tell you whether that container includes AI agents, models, prompts, tools, memory layers, or other agentic building blocks.

This module adds that missing inventory layer and ties it to the production graph through the `:Image` ontology label, so you can ask questions such as:

- Which production images contain AI agents?
- Which production images contain AIBOM components such as tools, models, datasets, and secrets?
- Which scans were successfully anchored to a concrete image already present in the graph?

### Input format

Each JSON file must be a raw AIBOM `1.0.0rc4` report with a top-level `aibom_analysis` object.

```json
{
  "aibom_analysis": {
    "metadata": {
      "...": "report-level metadata"
    },
    "sources": {
      "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository@sha256:...": {
        "...": "source-level inventory"
      }
    },
    "summary": {
      "...": "report-level summary"
    },
    "risk": {
      "...": "report-level risk summary"
    },
    "errors": []
  }
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `aibom_analysis` | Yes | Root payload for a raw AIBOM `1.0.0rc4` report. |
| `aibom_analysis.metadata` | Yes | Report-level metadata such as analyzer version, timing, model, and schema version. |
| `aibom_analysis.sources` | Yes | Map of scanned sources keyed by digest-qualified source reference. |
| `aibom_analysis.summary` | No | Report-level summary counts and severity fields. |
| `aibom_analysis.risk` | No | Report-level risk score and severity summary. |
| `aibom_analysis.errors` | No | Report-level error list. |

`aibom_analysis.sources` must be non-empty. Empty source maps are treated as
malformed input and fail AIBOM sync with a validation error.

Each source under `aibom_analysis.sources` should include:

- `source_name`
- `source_path`
- `summary`
- `metadata`
- `components`
- `relationships`

### Image linking behavior

AIBOM links scan results to concrete `:Image` nodes by digest, making the ingestion provider-agnostic across ECR, GCP Artifact Registry, GitLab Container Registry, and other supported registries.

- **Digest-qualified source keys** (`repo@sha256:...`): The digest is extracted directly from the source key and verified against `:Image` nodes via `_ont_digest`.
- **Tag-only source keys** (`repo:tag`): Not accepted for this ingestion flow.
- **Manifest list and image-tag anchors**: Not accepted as primary ingestion anchors for this module. The report must resolve to a concrete `:Image` digest already present in the graph.

If any source key is not digest-qualified, or if any digest-qualified source key
does not resolve to a concrete `:Image`, Cartography raises an error and fails
the AIBOM sync run.

### Current graph scope

This implementation currently ingests:

- `AIBOMSource`
- `AIBOMComponent`

and creates these relationships:

- `(:AIBOMSource)-[:SCANNED_IMAGE]->(:Image)`
- `(:AIBOMSource)-[:HAS_COMPONENT]->(:AIBOMComponent)`
- `(:AIBOMComponent)-[:DETECTED_IN]->(:Image)`
- `(:AIBOMComponent)-[:USES_MODEL]->(:AIBOMComponent)`
- `(:AIBOMComponent)-[:USES_TOOL]->(:AIBOMComponent)`
- `(:AIBOMComponent)-[:EXPOSES_TOOL]->(:AIBOMComponent)`
- `(:AIBOMComponent)-[:CUSTOM]->(:AIBOMComponent)`

Component-to-component relationships are loaded as standard relationships owned
by the source `AIBOMComponent` payload. During transform, report
`relationship_type` values are resolved onto target component id arrays such as
`uses_model_component_ids` and `uses_tool_component_ids`.

When the shared ontology analysis jobs run later in the overall sync, Cartography
also creates:

- `(:AIBOMSource)-[:RUNS_ON]->(:Container)`

Workflow nodes are still deferred in the current rc4 implementation.

### Prerequisite

Run image provider ingestion (ECR, GCP Artifact Registry, GitLab, etc.) before AIBOM ingestion so concrete `:Image` nodes with `_ont_digest` already exist in the graph. In the default sync order AIBOM runs after provider modules automatically.

### Results layout

The AIBOM module ingests every `*.json` file under the configured source as part of a single snapshot. Keep only the latest scan per image in the results location. If older reports for the same image are also present, their scans and detections will all be loaded in that snapshot because they share the same `update_tag`.

Cleanup is module-wide and runs only after a fully observed snapshot. If any
report fails to read, Cartography skips AIBOM cleanup for that run to avoid
deleting last-known-good data.

### Run with local files

```bash
cartography \
  --selected-modules aibom \
  --aibom-source /path/to/aibom-results
```

### Run with object storage

```bash
cartography \
  --selected-modules aibom \
  --aibom-source s3://my-aibom-bucket/reports/
```

`--aibom-source` also accepts `gs://bucket/prefix` and `azblob://account/container/prefix`.

### Observability counters

- `aibom_reports_processed`

### Example queries

Find images whose scanned source contains agent components:

```cypher
MATCH (source:AIBOMSource)-[:SCANNED_IMAGE]->(img:Image)
MATCH (source)-[:HAS_COMPONENT]->(component:AIBOMComponent)
WHERE component.category = 'agent'
RETURN source.image_uri, img._ont_digest, collect(component.name)
```

Find component-to-component relationships emitted by the AIBOM report:

```cypher
MATCH (source:AIBOMSource)-[:HAS_COMPONENT]->(src:AIBOMComponent)-[r]->(dst:AIBOMComponent)
WHERE type(r) IN ['USES_MODEL', 'USES_TOOL', 'EXPOSES_TOOL', 'CUSTOM']
RETURN source.source_key, src.name, type(r), dst.name
ORDER BY src.name, type(r), dst.name
```
