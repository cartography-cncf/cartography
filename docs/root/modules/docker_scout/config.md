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

1. Ensure your container images are already present in the ontology as `Image` nodes with `_ont_digest` populated. Docker Scout links recommendation reports to those ontology images.

   In practice, this usually means syncing the underlying registry modules first so the ontology pipeline can materialize `Image` nodes. For example, with AWS ECR:

    ```bash
    cartography --selected-modules aws --aws-requested-syncs ecr
    ```

### Generating scan results

Docker Scout ingestion now expects the standard text output produced by `docker scout recommendations`.

For each image, generate one text file with:

```bash
IMAGE="000000000000.dkr.ecr.us-east-1.amazonaws.com/my-app:latest"
OUTPUT_DIR="./docker-scout-results"
OUTPUT_FILE="${OUTPUT_DIR}/$(echo "$IMAGE" | tr '/:' '__').txt"

mkdir -p "$OUTPUT_DIR"
docker scout recommendations --output "$OUTPUT_FILE" "$IMAGE"
```

This produces the standard recommendation report used by Cartography to parse:

- the target image reference and short digest
- the current base image
- the recommended replacement tags
- the recommendation benefits and vulnerability deltas
- the ontology link key used to attach the report to an existing `(:Image)` node via `_ont_digest`

**Naming conventions**:

- Text files can be named using any convention.
- Cartography does not rely on the filename to identify the image.
- The report is linked from the `Target` digest in the file to an existing ontology `Image` node using `_ont_digest`.

### Configuring Cartography

#### Option 1: Local directory

Place the Docker Scout text result files in a directory and point Cartography at it:

```bash
cartography --selected-modules docker_scout \
    --docker-scout-source /path/to/results
```

Cartography will inspect non-hidden files under the provided directory recursively and ingest the ones that match the Docker Scout recommendation report format.

#### Option 2: Object storage

Upload the Docker Scout text result files to a supported object store and configure Cartography to read from it:

```bash
cartography --selected-modules docker_scout \
    --docker-scout-source s3://my-bucket/docker-scout-scans/
```

This requires the role running Cartography to have `s3:ListBucket`, `s3:GetObject` permissions for the bucket and prefix.

`--docker-scout-source` also accepts `gs://bucket/prefix` and `azblob://account/container/prefix`.

Deprecated local and S3 report-source flags remain accepted until Cartography v1.0.0 and emit warnings when used. New configurations should use `--docker-scout-source`.

### What Gets Created

For each report, Cartography creates:

- one `DockerScoutPublicImage` node for the current public base image
- one or more `DockerScoutPublicImageTag` nodes for the current and recommended tags
- a `BUILT_FROM` relationship from the current public image to its current base image entry
- `SHOULD_UPDATE_TO` relationships from the current public image to recommended base image tags
- a `BUILT_ON` relationship from the ontology `Image` node to the `DockerScoutPublicImage` node

### Required cloud permissions

| Resource | Permissions required |
|---|---|
| S3 bucket (if using S3 ingestion) | `s3:ListBucket`, `s3:GetObject` |
| ECR images (for scanning) | `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer` |
