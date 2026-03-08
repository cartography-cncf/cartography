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

### Supported input formats

Cartography accepts two JSON layouts. Both must contain the native `aibom_analysis` object produced by the scanner.

#### 1. Raw AIBOM output

Pass the scanner output as-is. Cartography reads `aibom_analysis.sources` and uses each source key as the image URI. This works when the scanner was invoked with a registry reference (e.g. `000000000000.dkr.ecr.us-east-1.amazonaws.com/repo:tag`) so the source key is already a valid image URI.

If a source key looks like a local filesystem path (absolute path, `./`, `../`, or `file://`), that source is skipped because it cannot be resolved to an ECR image.

#### 2. Envelope format (recommended)

Wrap the scanner output in a JSON envelope that explicitly provides the image URI. This is the recommended approach because:

- The scanner is often invoked against a local directory or extracted container filesystem, producing source keys that are local paths rather than registry references.
- The envelope lets your CI pipeline attach the correct registry URI after scanning.

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
| `image_uri` | Yes | ECR image URI (tag or digest). Overrides source keys from the scanner output. |
| `report` | Yes | Wrapper object containing the native `aibom_analysis`. |
| `scan_scope` | No | Path that was scanned inside the container (e.g. `/app`). Stored on components for context. |
| `scanner.name` | No | Scanner name. Defaults to `cisco-aibom`. |
| `scanner.version` | No | Scanner version. Falls back to `aibom_analysis.metadata.analyzer_version`. |

#### Resolution rules

1. If `image_uri` is present, it is used for all sources in the report.
1. Otherwise each `aibom_analysis.sources` key is used as the image URI.
1. Sources with local-path keys and no envelope `image_uri` are skipped.

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
