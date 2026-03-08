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

1. Raw AIBOM JSON output.
1. Envelope JSON with `image_uri` and `report` wrapper.

Recommended envelope format:

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
      "...": "native report"
    }
  }
}
```

Resolution rules:

1. If envelope fields exist, Cartography uses `image_uri` and `report`.
1. Otherwise Cartography uses raw `aibom_analysis` and infers source image URI from `aibom_analysis.sources` keys.
1. If inferred source looks like a local path and no envelope `image_uri` is provided, that source is skipped.

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
