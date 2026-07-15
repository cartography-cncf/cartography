# Trivy Configuration

## Prerequisites

Install Trivy by following the [official Trivy installation
guide](https://aquasecurity.github.io/trivy/latest/getting-started/installation/).
Populate the graph with the registry resources that you want to scan before
running the Trivy module. For AWS ECR:

```bash
cartography --selected-modules aws --aws-requested-syncs ecr
```

## Required Permissions

When scanning AWS ECR, the machine running Trivy needs these permissions:

| Cartography node label | Cloud permissions required to scan with Trivy |
|---|---|
| [AWSECRRepositoryImage](https://cartography-cncf.github.io/cartography/modules/aws/schema.html#ecrrepositoryimage) | `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer` |

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

Scan images with Trivy and put the JSON results in a local directory or
supported object store. Cartography requires these Trivy arguments:

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

JSON files can use any naming convention. Cartography determines which image a
scan belongs to from the scan content, not the filename. You can use an object
prefix to organize cloud results. For example:

- `s3://my-bucket/trivy-scans/123456789012.dkr.ecr.us-east-1.amazonaws.com/test-app:v1.2.3.json`
- `s3://my-bucket/trivy-scans/scan-12345.json`

Cartography supports scans identified by tag URIs such as `repo:tag` and digest
URIs such as `repo@sha256:abc123...`. Digest-qualified URIs support
multi-architecture images where each platform has its own digest. Cartography
matches scans to canonical images using the digest in `Metadata.RepoDigests`.

## Advanced Configuration

Deprecated local and S3 report-source flags remain accepted until Cartography
v1.0.0 and emit warnings when used. New configurations should use
`--trivy-source`.

## References

- [Trivy documentation](https://aquasecurity.github.io/trivy/latest/)
