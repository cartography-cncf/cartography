## AIBOM Configuration

The AIBOM module ingests pre-generated [Cisco AI BOM](https://github.com/cisco-ai-defense/aibom) JSON reports and maps them onto container images already present in Cartography.

Cartography does not run the scanner in this module. It only ingests JSON artifacts from local disk or supported object stores.

### Why this module exists

Traditional image inventory tells you what packages and vulnerabilities exist in a container. It does not tell you whether that container includes AI agents, models, prompts, tools, memory layers, or other agentic building blocks.

This module adds that missing inventory layer and ties it to the production graph through the `:Image` ontology label, so you can ask questions such as:

- Which production images contain AI agents?
- Which agents use tools, prompts, models, or memory?
- Which scans failed or did not match a known image in the graph?

### Input format

Each JSON file must be an envelope wrapping the native scanner output with the image URI that should be matched to the graph.

```json
{
  "image_uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:v1.0",
  "scan_scope": "/app",
  "scanner": {
    "name": "cisco-aibom",
    "version": "0.4.0"
  },
  "report": {
    "aibom_analysis": {
      "...": "native scanner output"
    }
  }
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `image_uri` | Yes | Image URI to map into the graph. Tag-based and digest-based URIs are both supported. |
| `report` | Yes | Wrapper object containing the native `aibom_analysis`. |
| `scan_scope` | No | Path or scope scanned inside the image or extracted filesystem. Stored on `AIBOMSource`. |
| `scanner.name` | No | Scanner name. Defaults to `cisco-aibom`. |
| `scanner.version` | No | Scanner version. Falls back to `aibom_analysis.metadata.analyzer_version`. |

The native source payload may optionally include:

- `workflows`
- `relationships`
- `source_kind`
- category-specific component fields such as `model_name`, `framework`, and `label`

The module preserves those optional fields when present.

### Image linking behavior

AIBOM links scan results to any node carrying the `:Image` ontology label, making it provider-agnostic across ECR, GCP Artifact Registry, GitLab Container Registry, and other supported registries.

- **Digest-based URIs** (`repo@sha256:...`): The digest is extracted directly and verified against `:Image` nodes via `_ont_digest`. No provider-specific traversal is needed.
- **Tag-based URIs** (`repo:tag`): A provider-specific fallback resolves the tag via `ECRRepositoryImage` → `ECRImage`. Single-platform images are returned directly. For manifest lists, the resolver traverses `CONTAINS_IMAGE` to return all child single-platform image digests, creating one-to-many relationships from a single source or component to multiple platform images.

### Provenance behavior

Cartography now preserves source provenance even when component inventory is not loaded:

- If a source has a non-`completed` status, Cartography loads `AIBOMSource` but skips components, workflows, and relationships.
- If `image_uri` does not resolve to an `Image` node, Cartography still loads `AIBOMSource` with `image_matched = false` for troubleshooting.

This makes stale coverage, failed scans, and mismatched image URIs visible in the graph instead of silently disappearing.

### Prerequisite

Run image provider ingestion (ECR, GCP Artifact Registry, GitLab, etc.) before AIBOM ingestion so `:Image` nodes with `_ont_digest` exist in the graph. For tag-based URI resolution, `ECRRepositoryImage` nodes must also exist. In the default sync order AIBOM runs after provider modules automatically.

### Results layout

The AIBOM module ingests every `*.json` file under the configured source as part of a single snapshot. Keep only the latest scan per image in the results location. If older reports for the same image are also present, their scans and detections will all be loaded in that snapshot because they share the same `update_tag`.

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

Deprecated local and S3 report-source flags remain accepted until Cartography v1.0.0 and emit warnings when used. New configurations should use `--aibom-source`.

### Observability counters

- `aibom_reports_processed`
- `aibom_sources_total`
- `aibom_sources_matched`
- `aibom_sources_unmatched`
- `aibom_sources_skipped_incomplete`
- `aibom_components_loaded_<category>`
- `aibom_relationships_loaded_<relationship_type>`
