## Trivy Configuration

[Trivy](https://aquasecurity.github.io/trivy/latest/) is a vulnerability scanner that can be used to scan images for vulnerabilities.

Currently, Cartography allows you to use Trivy to scan the following resources:

- [ECRImage](https://cartography-cncf.github.io/cartography/modules/aws/schema.html#ecrimage) (note that you scan ECRRepositoryImages but findings attach to their underlying ECRImage nodes)


To use Trivy with Cartography,

1. First ensure that your graph is populated with the resources that you want Trivy to scan.

    Doing this with AWS ECR looks like this:

    ```bash
    cartography --selected-modules aws --aws-requested-syncs ecr
    ```

1. Scan the images with Trivy, putting the JSON results in an S3 bucket.

    **Cartography expects Trivy to have been called with the following arguments**:

    - `--format json`: because Trivy's schema has a `fixed_version` field that is _super_ useful. This is the only format that Cartography will accept.
    - `--security-checks vuln`: because we only care about vulnerabilities.

    **Optional Trivy parameters to consider**:

    - `--ignore-unfixed`: if you want to ignore vulnerabilities that do not have a fixed version.
    - `--list-all-pkgs`: when present, Trivy will list all packages in the image, not just the ones that have vulnerabilities. This is useful for getting a complete inventory of packages in the image. Cartography will then attach all packages to the ECRImage node.

    **Naming conventions**:

    - JSON files can be named using any convention. Cartography determines which ECR image each scan belongs to by inspecting the scan content (see below), not the filename.

    - You can use an s3 object prefix to organize the results. For example if your bucket is `s3://my-bucket/` and you want to put the results in a folder called `trivy-scans/`, the full S3 object key could be `trivy-scans/123456789012.dkr.ecr.us-east-1.amazonaws.com/test-app:v1.2.3.json` or `trivy-scans/scan-12345.json`.

    **Digest-qualified URIs**:

    - Cartography supports scanning images by both tag URIs (e.g., `repo:tag`) and digest URIs (e.g., `repo@sha256:abc123...`).

    - This enables scanning of multi-architecture images where each platform (amd64, arm64, etc.) has its own digest.

    - Cartography matches scans to ECR images by inspecting the `ArtifactName`, `Metadata.RepoTags`, and `Metadata.RepoDigests` fields in the Trivy JSON output.

1. Configure Cartography to use the Trivy module.

    ```bash
    cartography --selected-modules trivy --trivy-s3-bucket my-bucket --trivy-s3-prefix trivy-scans/
    ```

    Cartography will then search s3://my-bucket/trivy-scans/ for all `.json` files and load them into the graph. Note that this requires the role running Cartography to have the `s3:ListObjects` and `s3:GetObject` permissions for the bucket and prefix.

    The `--trivy-s3-prefix` parameter is optional and defaults to an empty string.

1. Alternatively, place the JSON results on disk and point Cartography at the directory.

    ```bash
    cartography --selected-modules trivy --trivy-results-dir /path/to/trivy-results
    ```

    Cartography will ingest every `.json` file under the provided directory. Each scan is matched to an ECR image by inspecting the `ArtifactName`, `Metadata.RepoTags`, and `Metadata.RepoDigests` fields, so file names may contain any characters.

## Notes on running Trivy

- You can use [custom OPA policies](https://trivy.dev/latest/docs/configuration/filtering/#by-rego) with Trivy to filter the results. To do this, specify the path to your policy file using `--trivy-opa-policy-file-path`
    ```bash
    cartography --trivy-path /usr/local/bin/trivy --trivy-opa-policy-file-path /path/to/policy.rego
    ```

- Consider also running Trivy with `--timeout 15m` for larger images e.g. Java ones.

- You can use `--vuln-type os` to scan only operating system packages for vulnerabilities. These are more straightforward to fix than vulnerabilities in application packages. Eventually we'd recommend removing this flag so that you have visibility into both OS package and library package vulnerabilities.

- Refer to the [official Trivy installation guide](https://aquasecurity.github.io/trivy/latest/getting-started/installation/) for your operating system and for additional documentation.


### Required cloud permissions

Ensure that the machine running Trivy has the necessary permissions to scan your desired resources.


| Cartography Node label | Cloud permissions required to scan with Trivy |
|---|---|
| [ECRRepositoryImage](https://cartography-cncf.github.io/cartography/modules/aws/schema.html#ecrrepositoryimage) | `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer` |
