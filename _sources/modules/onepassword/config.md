# 1Password Configuration

Cartography reads snapshots that the open source
[1Password collector](https://github.com/subimagesec/collectors/tree/main/1password),
maintained by [Subimage](https://subimage.io), produces. Run the collector
first, then point Cartography at its output.

## Prerequisites

- A 1Password Business account
- The 1Password collector, running on a schedule in your environment. See its
  [setup guide](https://github.com/subimagesec/collectors/tree/main/1password#readme).

## Authentication

Cartography never authenticates to 1Password. The collector uses a 1Password
service account token. Cartography authenticates only to the storage that holds
the snapshots, with its usual provider credentials.

## Required Permissions

| Source | Permissions required |
|---|---|
| Local file or directory | Read access to the files |
| Amazon S3 | `s3:ListBucket` on the bucket and `s3:GetObject` on the prefix |
| Google Cloud Storage | `storage.objects.list` and `storage.objects.get` on the bucket |
| Azure Blob Storage | Storage Blob Data Reader on the container |

## Configure Cartography

Set `--onepassword-source` to one of the following:

- A snapshot `.json` file
- A local directory that contains snapshots
- An `s3://bucket/prefix`, `gs://bucket/prefix`, or
  `azblob://account/container/prefix` URI

Use a prefix that contains only 1Password snapshots. Cartography reads every
`.json` object under it on each sync, so have the collector overwrite one fixed
object per account rather than keep timestamped copies.

```{note}
The module is named `onepassword` because identifiers can't start with a
digit. `1password` isn't a valid Python module name or keyword argument, and
Neo4j labels such as `1PasswordUser` would need backticks in every query. Use
`onepassword` in `--selected-modules`, `--onepassword-source`, and the
`OnePassword*` node labels. 1Password's own Python SDK uses the same name.
```

## Run Cartography

```bash
cartography --selected-modules onepassword,ontology \
    --onepassword-source s3://example-snapshots/onepassword/
```

To test with a local snapshot:

```bash
cartography --selected-modules onepassword,ontology \
    --onepassword-source ./output/onepassword.json
```

Include `ontology` after `onepassword` to link 1Password users to canonical
users from your other identity sources.

## Input Artifacts

### Generate Input Artifacts

The collector writes one snapshot per run:

```bash
onepassword-collector \
    --account-id <account-uuid> \
    --vault-id <vault-uuid> \
    --output s3://example-snapshots/onepassword/snapshot.json
```

Repeat `--vault-id` for every vault to cover. The service account must have
**Read Items** access to each one.

### Input Format

Cartography accepts snapshots that use schema version `1.x` and have the status
`complete`. The collector repository documents the
[snapshot format](https://github.com/subimagesec/collectors/blob/main/1password/docs/format.md).

Each snapshot covers one account and the vaults the collector was configured to
read. Run one collector per account. When the source holds several snapshots
for the same account, Cartography ingests only the most recently collected one.
Anything that snapshot no longer contains is deleted from that account, so a
revoked grant disappears on the next sync. After you remove a vault from the
collector's scope and delete snapshots that still list it, the next sync removes
that vault from the graph.

Cartography stops before changing the graph if any snapshot in the source is
incomplete, malformed, or unreadable, uses an unsupported schema version, or
covers different vaults than another snapshot of the same account. It also
skips an account whose snapshot is older than the one already in the graph. An
older snapshot could otherwise restore access that 1Password already revoked.

`OnePasswordAccount.snapshot_collected_at` records when the collector finished.
If it falls behind your collection schedule, the snapshot is stale: check that
the collector still runs and that its output still reaches the source. The
graph shows access as of that time.

## Troubleshooting

| Error | Fix |
|---|---|
| `No 1Password snapshots found` | Check that the source path or prefix contains the collector's `.json` output. |
| `is not a 1Password collector snapshot` | Remove other JSON files from the prefix, or point to a narrower prefix. |
| `uses unsupported snapshot schema version` | Upgrade Cartography to a version that supports the collector's schema. |
| `cover different vaults` | Run one collector per account, and delete snapshots left from an earlier vault scope. |
| `Skipping 1Password account ... is older than the ingested snapshot` | Check why the source holds an older snapshot, such as a restored backup or a second collector. |
