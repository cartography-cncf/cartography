# BloodHound Configuration

Point Cartography at the output of a SharpHound CE collection. Cartography
only reads files; it never runs a collector or connects to Active Directory.

## Prerequisites

- Output from [SharpHound CE](https://github.com/SpecterOps/SharpHound), or
  another collector that writes BloodHound CE data version 6.
- Read access to the location holding that output.

```{note}
SharpHound is an offensive-security tool and endpoint protection may flag it.
Run it only with the directory owner's approval and in line with their
security policy.
```

## Configure Cartography

| Option | Description |
|---|---|
| `--bloodhound-source` | Required. A zip archive, a JSON file, or a directory or prefix holding either: a local path, `s3://bucket/prefix`, `gs://bucket/prefix` or `azblob://account/container/prefix`. |
| `--bloodhound-collected-at` | Optional. ISO 8601 collection time, for example `2026-10-12T14:30:15`. Needed only when the file names lack SharpHound's timestamp prefix, such as output written with `--randomfilenames`. |

## Run Cartography

```bash
cartography --neo4j-uri bolt://localhost:7687 \
            --selected-modules bloodhound \
            --bloodhound-source /path/to/20261012143015_BloodHound.zip
```

For output stored in S3:

```bash
cartography --neo4j-uri bolt://localhost:7687 \
            --selected-modules bloodhound \
            --bloodhound-source s3://my-security-bucket/bloodhound/
```

## Input Artifacts

### Generate Input Artifacts

Run SharpHound CE with the `All` or `Default` collection method and keep the
zip archive it writes:

```bash
SharpHound.exe --collectionmethods All
```

`DCOnly` also works, but it skips host-level data such as sessions and local
group membership.

### Input Format

- BloodHound CE JSON, data version 6. Legacy BloodHound (version 5 and
  earlier) is rejected.
- Each import needs `domains`, `users`, `groups` and `computers` data. `ous`,
  `gpos` and `containers` are imported when present. Certificate services data
  is skipped.
- A source may hold several collections, for example one archive per
  scheduled run. For each domain only the newest collection, by SharpHound's
  timestamp prefix, is imported and older ones are skipped, so new archives
  can be added beside old ones and a bucket lifecycle rule can expire them.
  Loose JSON files belong to the same collection when they share a directory
  and timestamp prefix.
- Archives and JSON files are streamed, so large forests do not need to fit in
  memory. Archives from object stores are downloaded to a temporary directory
  first.

## Troubleshooting

| Error | Cause |
|---|---|
| `contains N objects but its meta block declares M` or `has no meta block` | The file was cut short, usually by an interrupted copy or collection. Re-copy or re-collect it. |
| `is BloodHound data version 5` | The output came from legacy SharpHound. Use SharpHound CE. |
| `is missing ... data` | The collection method skipped object data. Re-run with `All` or `Default`. |
| `Cannot tell when ... was collected` | The file names have no timestamp prefix. Set `--bloodhound-collected-at`. |

A failed import leaves the previously imported data unchanged.
