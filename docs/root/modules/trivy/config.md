## Trivy Configuration

[Trivy](https://aquasecurity.github.io/trivy/latest/) is a vulnerability scanner for container images. Cartography ingests Trivy scan results and builds image lineage relationships using registry layer information.

### Quick Start

1. **Populate your graph** with container images (e.g., AWS ECR):
   ```bash
   cartography --selected-modules aws --aws-requested-syncs ecr
   ```

2. **Run Trivy scans** and save results as JSON:
   ```bash
   trivy image --format json --security-checks vuln <image-uri> > scan-results.json
   ```

   Required parameters:
   - `--format json`: Cartography only accepts JSON format
   - `--security-checks vuln`: Focus on vulnerabilities

3. **Ingest results** into Cartography:

   From S3:
   ```bash
   cartography --selected-modules trivy --trivy-s3-bucket my-bucket --trivy-s3-prefix scans/
   ```

   From disk:
   ```bash
   cartography --selected-modules trivy --trivy-results-dir /path/to/results
   ```

### Image Lineage

Cartography automatically builds parent-child relationships between container images by analyzing shared layers. This requires Docker with buildx support.

**Prerequisites:**
- Docker Desktop 18.09+ or Docker Engine 19.03+
- Verify: `docker buildx imagetools --help`

**How it works:**
1. Extracts layer information using `docker buildx imagetools inspect`
2. Identifies parent images based on shared layer prefixes
3. Creates `BUILT_FROM` relationships in the graph

**Configuration:**
```bash
# Disable lineage building (enabled by default)
cartography --selected-modules trivy --trivy-build-lineage false

# Specify platform for multi-arch images
cartography --selected-modules trivy --trivy-platform linux/arm64
```

### S3 Storage Format

When using S3, name files as `<image-uri>.json`:
- Image: `123456789.dkr.ecr.us-east-1.amazonaws.com/app:v1.0`
- S3 key: `123456789.dkr.ecr.us-east-1.amazonaws.com/app:v1.0.json`

### Disk Storage Format

Place `.json` files in any directory structure. The image URI is read from the `ArtifactName` field in each file.

### Additional Options

- **Include all packages** (not just vulnerable ones):
  ```bash
  trivy image --list-all-pkgs ...
  ```

- **Ignore unfixed vulnerabilities**:
  ```bash
  trivy image --ignore-unfixed ...
  ```

- **Set timeout for large images**:
  ```bash
  trivy image --timeout 15m ...
  ```

### Required Permissions

| Operation | AWS Permissions |
|-----------|----------------|
| Trivy scanning | `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer` |
| Layer extraction | `ecr:GetAuthorizationToken`, `ecr:DescribeImages` |
| S3 storage | `s3:ListBucket`, `s3:GetObject` |
