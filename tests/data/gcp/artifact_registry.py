MOCK_LOCATIONS = ["us-central1", "us-east1"]

MOCK_REPOSITORIES = [
    {
        "name": "projects/test-project/locations/us-central1/repositories/docker-repo",
        "format": "DOCKER",
        "mode": "STANDARD_REPOSITORY",
        "description": "Docker container repository",
        "sizeBytes": "1024000",
        "createTime": "2024-01-01T00:00:00Z",
        "updateTime": "2024-01-15T00:00:00Z",
        "cleanupPolicyDryRun": False,
        "vulnerabilityScanningConfig": {"enablementState": "ENABLED"},
    },
    {
        "name": "projects/test-project/locations/us-central1/repositories/maven-repo",
        "format": "MAVEN",
        "mode": "STANDARD_REPOSITORY",
        "description": "Maven artifacts repository",
        "sizeBytes": "512000",
        "createTime": "2024-01-02T00:00:00Z",
        "updateTime": "2024-01-16T00:00:00Z",
    },
]

# Manifest list data for multi-arch images (returned in imageManifests field)
MOCK_MANIFEST_LIST = [
    {
        "digest": "sha256:def456",  # This matches what Trivy reports in trivy_gcp_sample.py
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {
            "architecture": "amd64",
            "os": "linux",
        },
    },
    {
        "digest": "sha256:ghi789",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "platform": {
            "architecture": "arm64",
            "os": "linux",
            "variant": "v8",
        },
    },
]

MOCK_DOCKER_IMAGES = [
    {
        "name": "projects/test-project/locations/us-central1/repositories/docker-repo/dockerImages/my-app@sha256:abc123",
        "uri": "us-central1-docker.pkg.dev/test-project/docker-repo/my-app@sha256:abc123",
        "tags": ["latest", "v1.0.0"],
        "imageSizeBytes": "50000000",
        "mediaType": "application/vnd.oci.image.index.v1+json",
        "uploadTime": "2024-01-10T00:00:00Z",
        "buildTime": "2024-01-10T00:00:00Z",
        "updateTime": "2024-01-10T00:00:00Z",
        "imageManifests": MOCK_MANIFEST_LIST,
    },
]

MOCK_HELM_CHARTS = [
    {
        "name": "projects/test-project/locations/us-central1/repositories/docker-repo/dockerImages/my-chart@sha256:xyz789",
        "uri": "us-central1-docker.pkg.dev/test-project/docker-repo/my-chart@sha256:xyz789",
        "tags": ["0.1.0"],
        "imageSizeBytes": "5000000",
        "artifactType": "application/vnd.cncf.helm.config.v1+json",
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "uploadTime": "2024-01-11T00:00:00Z",
        "updateTime": "2024-01-11T00:00:00Z",
    },
]

MOCK_MAVEN_ARTIFACTS = [
    {
        "name": "projects/test-project/locations/us-central1/repositories/maven-repo/mavenArtifacts/com.example:my-lib:1.0.0",
        "pomUri": "gs://test-bucket/com/example/my-lib/1.0.0/my-lib-1.0.0.pom",
        "groupId": "com.example",
        "artifactId": "my-lib",
        "version": "1.0.0",
        "createTime": "2024-01-05T00:00:00Z",
        "updateTime": "2024-01-05T00:00:00Z",
    },
]

# Transformed manifest data for the my-app image (matches MOCK_DOCKER_IMAGES[0])
MOCK_PLATFORM_IMAGES = [
    {
        "id": "projects/test-project/locations/us-central1/repositories/docker-repo/dockerImages/my-app@sha256:abc123@sha256:def456",
        "digest": "sha256:def456",
        "architecture": "amd64",
        "os": "linux",
        "os_version": None,
        "os_features": None,
        "variant": None,
        "media_type": "application/vnd.oci.image.manifest.v1+json",
        "parent_artifact_id": "projects/test-project/locations/us-central1/repositories/docker-repo/dockerImages/my-app@sha256:abc123",
        "project_id": "test-project",
    },
    {
        "id": "projects/test-project/locations/us-central1/repositories/docker-repo/dockerImages/my-app@sha256:abc123@sha256:ghi789",
        "digest": "sha256:ghi789",
        "architecture": "arm64",
        "os": "linux",
        "os_version": None,
        "os_features": None,
        "variant": "v8",
        "media_type": "application/vnd.oci.image.manifest.v1+json",
        "parent_artifact_id": "projects/test-project/locations/us-central1/repositories/docker-repo/dockerImages/my-app@sha256:abc123",
        "project_id": "test-project",
    },
]
