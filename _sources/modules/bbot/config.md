# BBOT Configuration

Cartography ingests completed BBOT JSON event streams from a local path or
supported object store.

## Prerequisites

Install and configure [BBOT](https://www.blacklanternsecurity.com/bbot/), then
generate a report for targets you are authorized to assess.

## Required Permissions

Local reports need only filesystem read access. Object-store sources use
Cartography's existing provider authentication and require these permissions:

| Source | Permissions required |
|---|---|
| Amazon S3 | `s3:ListBucket`, `s3:GetObject` |
| Google Cloud Storage | Permission to list objects and read object data for the configured prefix |
| Azure Blob Storage | Permission to list blobs and read blob data for the configured container and prefix |

## Configure Cartography

Set `--bbot-source` to one of the following:

- A local `.json` or `.jsonl` report
- A local directory containing reports
- An `s3://bucket/prefix`, `gs://bucket/prefix`, or
  `azblob://account/container/prefix` object-store URI

## Run Cartography

For one local report:

```bash
cartography --selected-modules bbot,ontology \
    --bbot-source /path/to/bbot-output/output.json
```

For a directory containing reports:

```bash
cartography --selected-modules bbot,ontology \
    --bbot-source /path/to/bbot-reports
```

For object storage:

```bash
cartography --selected-modules bbot,ontology \
    --bbot-source s3://my-bucket/bbot-reports/
```

Include `ontology` after `bbot` to correlate observations with provider
resources. The default all-module sync already runs the stages in this order.

## Input Artifacts

### Generate Input Artifacts

BBOT writes its event stream to `output.json` in the scan output directory. For
example:

```bash
bbot -t example.com -p subdomain-enum
```

See the [BBOT scan documentation](https://www.blacklanternsecurity.com/bbot/Stable/scanning/)
for target, preset, and module configuration.

### Input Format

A complete stream begins with a `SCAN` event whose status is `STARTING` (or
`RUNNING` in older output) and ends with a `SCAN` event whose status is
`FINISHED`.

When a source contains multiple reports or appended scans, Cartography ingests
only the most recently completed scan, based on the `finished_at` value in its
final `SCAN` event. Incomplete scans are ignored. BBOT string event data is read
from `data`, while structured event data is read from `data_json`; the legacy
structured `data` form remains supported.

If any candidate report cannot be read or parsed, Cartography ingests the newest
completed scan it could read but skips cleanup for that sync, preserving
previously ingested nodes and relationships.
