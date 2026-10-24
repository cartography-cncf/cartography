# Trivy Configuration

## Prerequisites

Install Trivy by following the [official Trivy installation
guide](https://aquasecurity.github.io/trivy/latest/getting-started/installation/).
Populate the graph with the image or filesystem snapshot resources that you want
to scan before running the Trivy module. For AWS ECR:

```bash
cartography --selected-modules aws --aws-requested-syncs ecr
```

Trivy scans ECR repository images, while Cartography attaches findings to
their underlying `AWSECRImage` nodes.

For a source filesystem snapshot, check out the exact commit while retaining
the repository's Git metadata, then run:

```bash
trivy fs --format json --scanners vuln --list-all-pkgs /path/to/repository
```

Cartography uses `Metadata.RepoURL` and the full SHA in `Metadata.Commit` to
match the report to every `FilesystemSnapshot` for that repository revision.

For EC2 root filesystems, sync the instances before producing or importing VM
reports so their filesystem targets exist in the graph. Use the same AWS account
and region as the scan, for example:

```bash
cartography --selected-modules aws --aws-requested-syncs ec2:instance \
  --aws-regions us-east-1
```

EC2 discovery creates targets for eligible running Linux instances with an EBS
root volume. See [VM Reports](#vm-reports) for the scan and ingestion commands.

## Required Permissions

The AWS credentials used to generate reports need the following permissions.
The VM row includes root-volume lookup and temporary snapshot creation/cleanup
in addition to Trivy's snapshot reads.

| Cartography node label | Cloud permissions required to scan with Trivy |
|---|---|
| [AWSECRRepositoryImage](https://cartography-cncf.github.io/cartography/modules/aws/schema.html#awsecrrepositoryimage) | `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer` |
| `AWSEC2FilesystemSnapshot` | `ec2:DescribeInstances`, `ec2:DescribeSnapshots`, `ec2:CreateSnapshot`, `ec2:CreateTags`, `ec2:DeleteSnapshot`, `ebs:ListSnapshotBlocks`, `ebs:GetSnapshotBlock`; for encrypted volumes: `kms:Decrypt`, `kms:DescribeKey`, `kms:CreateGrant`, `kms:GenerateDataKeyWithoutPlaintext`, `kms:ReEncrypt` on the encryption key |

For customer-managed KMS keys, the key policy must also allow the scanning
principal to use the key. See the [AWS EBS direct API permissions
guide](https://docs.aws.amazon.com/ebs/latest/userguide/ebsapi-permissions.html)
for policy examples, including restricting grants with
`kms:GrantIsForAWSResource`.

Cartography's AWS module needs no new permissions to discover filesystem
targets: it uses the `DescribeInstances` data it already fetches. The snapshot
creation, deletion, EBS direct API, and KMS permissions above belong to the scan
producer; importing local JSON reports does not require them.

For reports in S3, the role running Cartography needs `s3:ListBucket` on the
configured bucket and `s3:GetObject` on objects under the configured prefix.

## Configure Cartography

Set `--trivy-source` to a local path, `s3://bucket/prefix`,
`gs://bucket/prefix`, or `azblob://account/container/prefix`. Cartography
ingests every `.json` file under the source.

## Run Cartography

For reports in an object store:

```bash
cartography --selected-modules trivy --trivy-source s3://my-bucket/trivy-scans/
```

For local reports:

```bash
cartography --selected-modules trivy --trivy-source /path/to/trivy-results
```

## Input Artifacts

### Generate Input Artifacts

Scan images or checked-out repositories with Trivy and put the JSON results in
a local directory or supported object store. Cartography requires these Trivy
arguments:

- `--format json`: Cartography only accepts JSON, including the useful
  `fixed_version` field.
- `--security-checks vuln`: Scan for vulnerabilities.

Optional Trivy arguments include:

- `--ignore-unfixed`: Ignore vulnerabilities without a fixed version.
- `--list-all-pkgs`: Include all packages in the image, not only packages with
  vulnerabilities. Cartography attaches all included packages to the canonical
  `Image` node.
- `--timeout 15m`: Allow additional time for larger images, such as Java images.
- `--vuln-type os`: Scan only operating system packages. Remove this option
  when you also want visibility into application library vulnerabilities.
- [Custom OPA policies](https://trivy.dev/latest/docs/configuration/filtering/#by-rego)
  can filter results before Cartography ingests the report.

### Input Format

JSON files can use any naming convention. Cartography determines which scan
target a report belongs to from the scan content, not the filename. You can use
an object prefix to organize cloud results. For example:

- `s3://my-bucket/trivy-scans/123456789012.dkr.ecr.us-east-1.amazonaws.com/test-app:v1.2.3.json`
- `s3://my-bucket/trivy-scans/scan-12345.json`

Cartography supports scans identified by tag URIs such as `repo:tag` and digest
URIs such as `repo@sha256:abc123...`. Digest-qualified URIs support
multi-architecture images where each platform has its own digest. Cartography
matches scans to canonical images using the digest in `Metadata.RepoDigests`.

Filesystem reports must use `ArtifactType` `filesystem` or `repository` and
include `Metadata.RepoURL` plus a 40-character `Metadata.Commit`. Reports without
an exact graph match are skipped.

### VM Reports

#### Report identity

VM reports use `ArtifactType: "vm"`. Before ingestion, the scan producer must
add `Metadata.FilesystemSnapshotId` containing the stable graph target ID:

```json
{
  "ArtifactType": "vm",
  "ArtifactName": "ebs:snap-0123456789abcdef0",
  "Metadata": {
    "FilesystemSnapshotId": "aws:ec2-rootfs:i-0123456789abcdef0"
  }
}
```

This example shows the identity fields; retain the report's other metadata and
results. Trivy does not add `FilesystemSnapshotId` itself. The target must already
exist as a `FilesystemSnapshot` with `_ont_kind="rootfs"`, connected by
`(ComputeInstance)-[:SCANNED_AS]->(FilesystemSnapshot)`. EC2 discovery creates
these targets before report ingestion.

Each EC2 target stores the root EBS `volume_id` and links to that volume through
`(FilesystemSnapshot)-[:SNAPSHOT_OF]->(AWSEBSVolume:BlockStorage)`. If the root
volume is replaced, the next EC2 sync updates this property and relationship
while keeping the target ID stable.

After successfully ingesting a VM report, Cartography records its provenance on
the target:

| Target property | Trivy report field |
|---|---|
| `trivy_snapshot_id` | `ArtifactName`, with an optional `ebs:` prefix removed |
| `trivy_scan_created_at` | `CreatedAt`, the report creation timestamp |
| `trivy_version` | `Trivy.Version` |

These fields describe the most recently ingested VM report, including reports
with zero vulnerabilities. Missing fields remain unknown and clear any previous
value; Cartography does not substitute the import time for the scan time. EC2
discovery preserves these fields. The target's `lastupdated` remains the EC2
discovery timestamp. Supply one current report per target to avoid importing
older results over newer results.

Cartography uses this stable ID because the temporary EBS snapshot in
`ArtifactName` can change on every scan. Missing, invalid, or unmatched IDs are
skipped with a warning. VM reports follow the existing filesystem-report cleanup
rules. A successful report with zero vulnerabilities clears that target's old
findings. Cleanup is not limited to target IDs in the batch: stale data for
filesystem targets without reports can also be removed. Supply the complete set
of reports whose results should be retained. Read or parse failures, or a batch
with no matching reports, skip cleanup.

#### Scan an EC2 root filesystem

First complete the EC2 sync in [Prerequisites](#prerequisites). Install the AWS
CLI and `jq` alongside Trivy, and configure AWS credentials for the instance's
account. Choose an eligible instance with a supported root filesystem, as
described in the limits below.

Run the following in Bash, replacing `instance_id` and `scan_region`. It finds
the root volume, creates a tagged temporary EBS snapshot, waits for it to be
ready, scans it, and stamps the stable target ID while preserving all other
report fields. The subshell's exit trap deletes the snapshot on success or
failure, including when Trivy fails. If deletion fails, it prints the snapshot
ID for manual cleanup and exits with an error.

```bash
(
  set -euo pipefail
  instance_id="i-0123456789abcdef0"
  scan_region="us-east-1"
  report_dir="./trivy-vm-reports"
  scan_work_dir="$(mktemp -d)"
  snapshot_id=""

  cleanup() {
    scan_status=$?
    if [[ -n "$snapshot_id" ]]; then
      if ! aws ec2 delete-snapshot --region "$scan_region" \
        --snapshot-id "$snapshot_id"; then
        echo "Delete snapshot $snapshot_id in $scan_region manually." >&2
        scan_status=1
      fi
    fi
    rm -rf "$scan_work_dir"
    exit "$scan_status"
  }
  trap cleanup EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM

  instance_json="$(aws ec2 describe-instances --region "$scan_region" \
    --instance-ids "$instance_id" --output json)"
  volume_id="$(jq -er '
    .Reservations[0].Instances[0]
    | .RootDeviceName as $root
    | .BlockDeviceMappings[]
    | select(.DeviceName == $root)
    | .Ebs.VolumeId // empty
  ' <<< "$instance_json")"

  snapshot_id="$(aws ec2 create-snapshot --region "$scan_region" \
    --volume-id "$volume_id" \
    --description "Cartography rootfs scan for $instance_id" \
    --tag-specifications 'ResourceType=snapshot,Tags=[{Key=cartography:scan,Value=true}]' \
    --query SnapshotId --output text)"
  aws ec2 wait snapshot-completed --region "$scan_region" \
    --snapshot-ids "$snapshot_id"

  trivy vm --aws-region "$scan_region" --format json --scanners vuln \
    --list-all-pkgs --timeout 30m --output "$scan_work_dir/raw.json" \
    "ebs:$snapshot_id"
  jq --arg id "aws:ec2-rootfs:$instance_id" \
    '.Metadata.FilesystemSnapshotId = $id' \
    "$scan_work_dir/raw.json" > "$scan_work_dir/report.json"

  mkdir -p "$report_dir"
  mv "$scan_work_dir/report.json" "$report_dir/$instance_id.json"
)
```

Only the completed, stamped report is placed in `trivy-vm-reports`; the raw
report stays outside the ingestion directory. After the script succeeds, import
the report into the same Neo4j database used for EC2 discovery, adding your
usual Neo4j connection options to both Cartography commands as needed:

```bash
cartography --selected-modules trivy --trivy-source ./trivy-vm-reports/
```

The temporary EBS snapshot is already deleted at this point. Cartography needs
only the saved JSON and the stable filesystem target in the graph.

#### Limits

- Trivy's VM mode is experimental and may change without backwards
  compatibility. Its direct disk reader supports ext2, ext3, ext4, and XFS;
  LVM and ZFS are unsupported. See [Trivy's VM scanning
  documentation](https://trivy.dev/docs/latest/guide/target/vm/).
- This workflow scans the instance's root EBS volume only, not attached data
  volumes. EC2 discovery excludes Windows, macOS, stopped instances, and
  instances identified by Kubernetes tags. It cannot detect unsupported
  filesystems such as LVM or ZFS from EC2 metadata alone.
- Kubernetes exclusion relies on the `eks:cluster-name`,
  `alpha.eksctl.io/cluster-name`, or `kubernetes.io/cluster/` tags. Self-managed
  Kubernetes nodes without these tags and ECS container instances can still
  receive targets. Scanning those hosts alongside their container images can
  produce overlapping package and vulnerability results.
- Encrypted volumes require access to their KMS key. A missing permission is a
  scan failure, not a report with zero vulnerabilities; do not import an empty
  replacement report after a failed scan.

## Advanced Configuration

Deprecated local and S3 report-source flags remain accepted until Cartography
v1.0.0 and emit warnings when used. New configurations should use
`--trivy-source`.

## References

- [Trivy documentation](https://aquasecurity.github.io/trivy/latest/)
