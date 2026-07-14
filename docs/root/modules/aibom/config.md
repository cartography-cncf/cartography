## AIBOM Configuration

The AIBOM module ingests pre-generated [Cisco AI BOM](https://github.com/cisco-ai-defense/aibom) JSON reports and maps them onto container images or source-code repositories already present in Cartography.

Cartography does not run the scanner in this module. It only ingests JSON artifacts from local disk or supported object stores.

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

### Target linking behavior

AIBOM validates every source against an existing graph node before loading any
data:

- **Digest-qualified image references** (`repo@sha256:...`): The digest must
  match an existing `Image._ont_digest`.
- **Other source keys**: The complete value is treated as a repository URI and
  must match `GitHubRepository.url` or `GitLabProject.web_url`.
- **Tag-only image references** (`repo:tag`): These do not identify a concrete
  image and are interpreted as repository URIs. They are rejected unless an
  existing repository node has that exact URI.
- **Manifest lists and image tags**: These are not valid image anchors. Image
  reports must resolve to a concrete `Image` digest.

If any source key fails to resolve, Cartography raises an error and rejects the
entire report rather than loading a partial source graph.

### Prerequisite

Run the applicable provider ingestion before AIBOM:

- Image reports require concrete `Image` nodes populated by ECR, GCP Artifact
  Registry, GitLab Container Registry, or another image provider.
- Repository reports require matching `GitHubRepository` or `GitLabProject`
  nodes.

In the default sync order, AIBOM runs after provider modules automatically.

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
