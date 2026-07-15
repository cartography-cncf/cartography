# AIBOM Configuration

## Prerequisites

Run the applicable provider ingestion before AIBOM:

- Image reports require concrete `Image` nodes populated by ECR, GCP Artifact
  Registry, GitLab Container Registry, or another image provider.
- Repository reports require matching `GitHubRepository` or `GitLabProject`
  nodes.

In the default sync order, AIBOM runs after provider modules automatically.

## Configure Cartography

Set `--aibom-source` to a local directory or supported object storage URI.
Supported URI schemes include `s3://`, `gs://`, and `azblob://`.

## Run Cartography

Run with local files:

```bash
cartography \
  --selected-modules aibom \
  --aibom-source /path/to/aibom-results
```

Run with object storage:

```bash
cartography \
  --selected-modules aibom \
  --aibom-source s3://my-aibom-bucket/reports/
```

## Input Artifacts

Cartography ingests pre-generated
[Cisco AI BOM](https://github.com/cisco-ai-defense/aibom) JSON reports. It
does not run the scanner.

### Generate Input Artifacts

Generate AIBOM reports before running Cartography and place the resulting JSON
files in the configured local directory or object storage location. Keep only
the latest scan for each image in that location.

### Input Format

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
| `aibom_analysis.sources` | Yes | Map keyed by a digest-qualified image reference or a GitHub/GitLab repository URI. |
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
