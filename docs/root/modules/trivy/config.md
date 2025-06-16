## Trivy Configuration

[Trivy](https://aquasecurity.github.io/trivy/latest/) is a vulnerability scanner that can be used to scan images for vulnerabilities.

Currently, Cartography allows you to use Trivy to scan the following resources:

- [ECRRepositoryImage](https://cartography-cncf.github.io/cartography/modules/aws/schema.html#ecrrepositoryimage)


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

    - Each image URI should have its own S3 object key with the following naming convention: `<ECR Image URI>.json`. For example, if you have an ECR image URI of `123456789012.dkr.ecr.us-east-1.amazonaws.com/test-app:v1.2.3`, the S3 object key would be `123456789012.dkr.ecr.us-east-1.amazonaws.com/test-app:v1.2.3.json`.

    - You can also use an s3 object prefix to organize the results. For example if your bucket is `s3://my-bucket/` and you want to put the results in a folder called `trivy-scans/`, the full S3 object key would be `trivy-scans/123456789012.dkr.ecr.us-east-1.amazonaws.com/test-app:v1.2.3.json`.

1. Configure Cartography to use the Trivy module.

    ```bash
    cartography --selected-modules trivy --trivy-s3-bucket my-bucket --trivy-s3-prefix trivy-scans/
    ```

    Cartography will then search s3://my-bucket/trivy-scans/ for JSON files with the naming convention `<ECR Image URI>.json` and load them into the graph. Note that this requires the role running Cartography to have the `s3:ListObjects` and `s3:GetObject` permissions for the bucket and prefix.

    The `--trivy-s3-prefix` parameter is optional and defaults to an empty string.

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
