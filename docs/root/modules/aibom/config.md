## AIBOM Configuration

The AIBOM module ingests pre-generated [Cisco AI BOM](https://github.com/cisco-ai-defense/aibom) JSON reports and catalogs AI components discovered in container codebases.

Cartography does not run the scanner in this module. It only ingests JSON artifacts from local disk or S3.

### Why this module exists

Container vulnerability inventory tells you what software is present. It does not tell you whether an image contains AI agent logic, tool usage, or related AI workflows.

This module adds that missing layer by mapping AIBOM detections to container images already present in the graph.

### ECR-first linking behavior

AIBOM detections are linked to the most canonical `ECRImage` already in the graph:

1. Prefer `ECRImage` nodes where `type = "manifest_list"`.
1. Fall back to `ECRImage` nodes where `type = "image"` only when no manifest list exists for the tagged image.

This intentionally avoids duplicating detections across platform-specific child images (`amd64`, `arm64`) for the same logical image tag while still supporting single-platform images.

### Input format

Each JSON file must be an envelope wrapping the native scanner output with the ECR image URI. The scanner is typically invoked against a local directory or extracted container filesystem, so source keys inside the report are local paths. The envelope lets your CI pipeline attach the correct registry URI after scanning.

```json
{
  "image_uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:v1.0",
  "scan_scope": "/app/app",
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
| `image_uri` | Yes | ECR image URI (tag or digest). Used to link detections to the graph. |
| `report` | Yes | Wrapper object containing the native `aibom_analysis`. |
| `scan_scope` | No | Path that was scanned inside the container (e.g. `/app`). Stored on components for context. |
| `scanner.name` | No | Scanner name. Defaults to `cisco-aibom`. |
| `scanner.version` | No | Scanner version. Falls back to `aibom_analysis.metadata.analyzer_version`. |

### Prerequisite

Run ECR ingestion before AIBOM ingestion so `ECRRepositoryImage` and `ECRImage` nodes exist. In the default sync order AIBOM runs after AWS automatically.

### Results layout

The AIBOM module ingests every `*.json` file under the configured directory or S3 prefix as part of a single snapshot. Keep only the latest scan per image in the results location. If older reports for the same image are also present, their detections will be included in the graph and cleanup will not remove them because they share the same `update_tag`.

### Run with local files

```bash
cartography \
  --selected-modules aibom \
  --aibom-results-dir /path/to/aibom-results
```

### Run with S3

```bash
cartography \
  --selected-modules aibom \
  --aibom-s3-bucket my-aibom-bucket \
  --aibom-s3-prefix reports/
```

`--aibom-s3-prefix` is optional and defaults to an empty prefix.

### Observability counters

- `aibom_reports_processed`
- `aibom_sources_total`
- `aibom_sources_matched`
- `aibom_sources_unmatched`
- `aibom_sources_skipped_incomplete`
- `aibom_components_loaded_<category>`
