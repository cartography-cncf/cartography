## BBOT Configuration

[BBOT](https://www.blacklanternsecurity.com/bbot/) discovers internet-facing assets and security findings. Cartography ingests completed BBOT JSON event streams from a local path or supported object store.

### Generate a report

BBOT writes its event stream to `output.json` in the scan output directory. A complete stream begins with a `SCAN` event whose status is `RUNNING` and ends with a `SCAN` event whose status is `FINISHED`.

For example:

```bash
bbot -t example.com -p subdomain-enum
```

See the [BBOT scan documentation](https://www.blacklanternsecurity.com/bbot/Stable/scanning/) for target, preset, and module configuration. Only scan targets that you are authorized to assess.

### Configure Cartography

For one local report:

```bash
cartography --selected-modules bbot,ontology \
    --bbot-source /path/to/bbot-output/output.json
```

For a directory containing `.json` or `.jsonl` reports:

```bash
cartography --selected-modules bbot,ontology \
    --bbot-source /path/to/bbot-reports
```

For object storage:

```bash
cartography --selected-modules bbot,ontology \
    --bbot-source s3://my-bucket/bbot-reports/
```

`--bbot-source` also accepts `gs://bucket/prefix` and `azblob://account/container/prefix`. Cartography uses its existing AWS, GCP, or Azure authentication configuration to list and read those reports.

When a source contains multiple reports or appended scans, Cartography ingests only the most recently completed scan, based on the `finished_at` value in its final `SCAN` event. Incomplete scans are ignored. BBOT string event data is read from `data`, while structured event data is read from `data_json`; the legacy structured `data` form remains supported.

Include `ontology` after `bbot` to correlate observed DNS names and public IP addresses with provider resources already present in the graph. The default all-module sync already runs them in this order.

### Supported event types

Cartography currently ingests these BBOT event types:

- `SCAN`
- `DNS_NAME`
- `IP_ADDRESS`
- `IP_RANGE`
- `OPEN_TCP_PORT`
- `URL`
- `ASN`
- `TECHNOLOGY`
- `EMAIL_ADDRESS`
- `ORG_STUB`
- `SOCIAL`
- `STORAGE_BUCKET`
- `FINDING`

Other event types are logged and skipped.

### Snapshot behavior

The selected completed scan is treated as the current BBOT snapshot. Stable assets and relationships are merged in place, preserving `firstseen` and advancing `lastupdated`. Nodes or associations absent from the selected scan are deleted. If an asset later reappears, it is recreated with a new `firstseen`; historical absence tracking is not retained.

### Object-store permissions

| Source | Permissions required |
|---|---|
| Amazon S3 | `s3:ListBucket`, `s3:GetObject` |
| Google Cloud Storage | Permission to list objects and read object data for the configured prefix |
| Azure Blob Storage | Permission to list blobs and read blob data for the configured container and prefix |
