## Docker Scout Configuration

[Docker Scout](https://docs.docker.com/scout/) is a vulnerability scanner that analyzes container images for security issues in base image packages.

Currently, Cartography allows you to use Docker Scout to scan the following resources:

- [ECRImage](https://cartography-cncf.github.io/cartography/modules/aws/schema.html#ecrimage)
- [GCPArtifactRegistryContainerImage](https://cartography-cncf.github.io/cartography/modules/gcp/schema.html#gcpartifactregistrycontainerimage)
- [GCPArtifactRegistryPlatformImage](https://cartography-cncf.github.io/cartography/modules/gcp/schema.html#gcpartifactregistryplatformimage)
- [GitLabContainerImage](https://cartography-cncf.github.io/cartography/modules/gitlab/schema.html#gitlabcontainerimage)

### Prerequisites

1. Install the [Docker Scout CLI plugin](https://docs.docker.com/scout/install/).

1. Authenticate with Docker Scout. You need a Docker Hub account with Scout access:

    ```bash
    docker login
    ```

    For CI environments, use a [Docker Hub access token](https://docs.docker.com/security/for-developers/access-tokens/):

    ```bash
    echo "$DOCKER_HUB_TOKEN" | docker login --username "$DOCKER_HUB_USERNAME" --password-stdin
    ```

1. Ensure the container image registry nodes (e.g., ECR, GCP Artifact Registry, GitLab) are already synced into the graph so Docker Scout can create relationships to them. For example, with AWS ECR:

    ```bash
    cartography --selected-modules aws --aws-requested-syncs ecr
    ```

### Generating scan results

Docker Scout ingestion requires pre-generated JSON files containing the scan results for each image. Each file must be a JSON object with two keys: `sbom` and `cves`.

For each image, run the following commands and combine the output:

```bash
IMAGE="000000000000.dkr.ecr.us-east-1.amazonaws.com/my-app:latest"

# Generate the combined JSON file
SBOM=$(docker scout sbom --format json "$IMAGE")
CVES=$(docker scout cves --only-base --format sbom "$IMAGE")
jq -n --argjson sbom "$SBOM" --argjson cves "$CVES" \
    '{sbom: $sbom, cves: $cves}' > results/my-app.json
```

**Required Docker Scout arguments**:

- `docker scout sbom --format json`: produces the SBOM containing image metadata (digest, base image annotations).
- `docker scout cves --only-base --format sbom`: produces the vulnerability list for base image packages. The `--only-base` flag restricts results to the public base image layer.

**Naming conventions**:

- JSON files can be named using any convention. Cartography determines which image each scan belongs to by inspecting the image digest in the SBOM data, not the filename.

### Configuring Cartography

#### Option 1: Local directory

Place the JSON result files in a directory and point Cartography at it:

```bash
cartography --selected-modules docker_scout \
    --docker-scout-results-dir /path/to/results
```

Cartography will ingest every `.json` file under the provided directory (recursively).

#### Option 2: S3 bucket

Upload the JSON result files to an S3 bucket and configure Cartography to read from it:

```bash
cartography --selected-modules docker_scout \
    --docker-scout-s3-bucket my-bucket \
    --docker-scout-s3-prefix docker-scout-scans/
```

This requires the role running Cartography to have `s3:ListBucket`, `s3:GetObject` permissions for the bucket and prefix.

The `--docker-scout-s3-prefix` parameter is optional and defaults to an empty string.

### Required cloud permissions

| Resource | Permissions required |
|---|---|
| S3 bucket (if using S3 ingestion) | `s3:ListBucket`, `s3:GetObject` |
| ECR images (for scanning) | `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer` |
