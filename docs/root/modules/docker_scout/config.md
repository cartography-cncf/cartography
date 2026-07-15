# Docker Scout Configuration

## Prerequisites

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

## Required Permissions

For S3 report ingestion, grant the role running Cartography `s3:ListBucket`
and `s3:GetObject` for the report bucket and prefix.

Scanning private ECR images requires `ecr:GetAuthorizationToken`,
`ecr:BatchGetImage`, and `ecr:GetDownloadUrlForLayer`.

## Configure Cartography

Set `--docker-scout-source` to a local directory or supported object storage
URI. Supported URI schemes include `s3://`, `gs://`, and `azblob://`.

## Run Cartography

Run with local result files:

```bash
cartography \
  --selected-modules docker_scout \
  --docker-scout-source /path/to/results
```

Run with object storage:

```bash
cartography \
  --selected-modules docker_scout \
  --docker-scout-source s3://my-bucket/docker-scout-scans/
```

## Input Artifacts

Docker Scout ingestion now expects the standard text output produced by `docker scout recommendations`.

### Generate Input Artifacts

Generate one text file for each image:

```bash
IMAGE="000000000000.dkr.ecr.us-east-1.amazonaws.com/my-app:latest"
OUTPUT_DIR="./docker-scout-results"
OUTPUT_FILE="${OUTPUT_DIR}/$(echo "$IMAGE" | tr '/:' '__').txt"

mkdir -p "$OUTPUT_DIR"
docker scout recommendations --output "$OUTPUT_FILE" "$IMAGE"
```

### Input Format

Cartography parses these fields from each standard recommendation report:

- the target image reference and short digest
- the current base image
- the recommended replacement tags
- the recommendation benefits and vulnerability deltas

Text files can use any filename. Cartography identifies the image from the
`Target` digest in the report and links it to an existing ontology `Image`
node through `_ont_digest`. It recursively inspects non-hidden files under the
configured source and ingests files that match the recommendation report
format.

## Advanced Configuration

Deprecated local and S3 report-source flags remain accepted until Cartography v1.0.0 and emit warnings when used. New configurations should use `--docker-scout-source`.

## References

- [Docker Scout](https://docs.docker.com/scout/)
- [Docker Scout CLI installation](https://docs.docker.com/scout/install/)
- [Docker Hub access tokens](https://docs.docker.com/security/for-developers/access-tokens/)
