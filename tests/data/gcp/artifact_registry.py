from copy import deepcopy

MOCK_LOCATIONS = ["us-central1", "us-east1"]

MOCK_SUPPLY_CHAIN_IMAGE_DIGEST = (
    "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
)
MOCK_SUPPLY_CHAIN_IMAGE_DIGEST_HEX = MOCK_SUPPLY_CHAIN_IMAGE_DIGEST.split(":", 1)[1]
MOCK_SUPPLY_CHAIN_IMAGE_URI = (
    "us-central1-docker.pkg.dev/test-project/docker-repo/widgets-api"
    f"@{MOCK_SUPPLY_CHAIN_IMAGE_DIGEST}"
)
MOCK_SUPPLY_CHAIN_IMAGE_ARTIFACT_NAME = (
    "projects/test-project/locations/us-central1/repositories/docker-repo/"
    f"dockerImages/widgets-api@{MOCK_SUPPLY_CHAIN_IMAGE_DIGEST}"
)
MOCK_SUPPLY_CHAIN_IMAGE_MANIFEST_URL = (
    "https://us-central1-docker.pkg.dev/v2/test-project/docker-repo/"
    f"widgets-api/manifests/{MOCK_SUPPLY_CHAIN_IMAGE_DIGEST}"
)
MOCK_SUPPLY_CHAIN_IMAGE_REFERRERS_URL = (
    "https://us-central1-docker.pkg.dev/v2/test-project/docker-repo/"
    f"widgets-api/referrers/{MOCK_SUPPLY_CHAIN_IMAGE_DIGEST}"
)
MOCK_SUPPLY_CHAIN_SBOM_URI = (
    "us-central1-docker.pkg.dev/test-project/docker-repo/"
    "github.com/example/widgets/cmd/server@sha256:sbommanifest"
)
MOCK_SUPPLY_CHAIN_MISSING_SBOM_URI = (
    "us-central1-docker.pkg.dev/test-project/docker-repo/"
    "github.com/example/missing/cmd/server@sha256:missing"
)
MOCK_SUPPLY_CHAIN_SBOM_MANIFEST_URL = (
    "https://us-central1-docker.pkg.dev/v2/test-project/docker-repo/"
    "github.com/example/widgets/cmd/server/manifests/sha256:sbommanifest"
)
MOCK_SUPPLY_CHAIN_SBOM_BLOB_URL = (
    "https://us-central1-docker.pkg.dev/v2/test-project/docker-repo/"
    "github.com/example/widgets/cmd/server/blobs/sha256:sbom"
)
MOCK_SUPPLY_CHAIN_DIGEST_SBOM_MANIFEST_URL = (
    "https://us-central1-docker.pkg.dev/v2/test-project/docker-repo/"
    f"widgets-api/manifests/sha256-{MOCK_SUPPLY_CHAIN_IMAGE_DIGEST_HEX}.sbom"
)
MOCK_SUPPLY_CHAIN_DIGEST_SBOM_BLOB_URL = (
    "https://us-central1-docker.pkg.dev/v2/test-project/docker-repo/"
    "widgets-api/blobs/sha256:sbom"
)
MOCK_SPDX_SBOM_MANIFEST = {
    "layers": [
        {
            "mediaType": "text/spdx+json",
            "digest": "sha256:sbom",
        },
    ],
}

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
    {
        "name": "projects/test-project/locations/us-east1/repositories/apt-repo",
        "format": "APT",
        "mode": "STANDARD_REPOSITORY",
        "description": "APT packages repository",
        "sizeBytes": "256000",
        "createTime": "2024-01-03T00:00:00Z",
        "updateTime": "2024-01-17T00:00:00Z",
    },
    {
        "name": "projects/test-project/locations/us-east1/repositories/yum-repo",
        "format": "YUM",
        "mode": "STANDARD_REPOSITORY",
        "description": "YUM packages repository",
        "sizeBytes": "384000",
        "createTime": "2024-01-04T00:00:00Z",
        "updateTime": "2024-01-18T00:00:00Z",
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

MOCK_SINGLE_IMAGE_CONFIG_DIGEST = (
    "sha256:0000000000000000000000000000000000000000000000000000000000000abc"
)
MOCK_SINGLE_IMAGE_MANIFEST = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.oci.image.manifest.v1+json",
    "config": {
        "mediaType": "application/vnd.oci.image.config.v1+json",
        "digest": MOCK_SINGLE_IMAGE_CONFIG_DIGEST,
        "size": 4096,
    },
    "layers": [
        {
            "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
            "digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "size": 8192,
        },
    ],
}

MOCK_SINGLE_IMAGE_CONFIG = {
    "architecture": "arm64",
    "os": "linux",
    "variant": "v8",
    "created": "2024-01-10T00:00:00Z",
    "config": {
        "Labels": {
            "org.opencontainers.image.source": "https://github.com/example/widgets.git",
            "org.opencontainers.image.revision": "0123456789abcdef",
        },
    },
    "rootfs": {
        "type": "layers",
        "diff_ids": [
            "sha256:2222222222222222222222222222222222222222222222222222222222222222",
        ],
    },
    "history": [
        {
            "created": "2024-01-10T00:00:00Z",
            "created_by": "COPY app /app",
        },
    ],
}

MOCK_SUPPLY_CHAIN_IMAGE_CONFIG_URL = (
    "https://us-central1-docker.pkg.dev/v2/test-project/docker-repo/"
    f"widgets-api/blobs/{MOCK_SINGLE_IMAGE_CONFIG_DIGEST}"
)


def mock_single_image_config_without_labels():
    config = deepcopy(MOCK_SINGLE_IMAGE_CONFIG)
    config["config"]["Labels"] = {}
    return config


def mock_spdx_sbom(
    image_digest=MOCK_SUPPLY_CHAIN_IMAGE_DIGEST,
    document_describes=None,
    packages=None,
):
    return {
        "spdxVersion": "SPDX-2.3",
        "name": f"sbom-{image_digest}",
        "documentNamespace": f"https://example.test/sbom/{image_digest}",
        "documentDescribes": document_describes or ["SPDXRef-RootPackage"],
        "packages": packages
        or [
            {
                "name": "github.com/example/widgets",
                "SPDXID": "SPDXRef-RootPackage",
                "downloadLocation": "https://github.com/example/widgets.git",
            },
        ],
    }


def mock_ko_spdx_sbom(image_digest=MOCK_SUPPLY_CHAIN_IMAGE_DIGEST):
    image_package_id = "SPDXRef-Package-sha256-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    source_package_id = "SPDXRef-Package-github.com.example.widgets-v1.0.0"
    return {
        "spdxVersion": "SPDX-2.3",
        "name": f"sbom-{image_digest}",
        "documentNamespace": f"https://example.test/sbom/{image_digest}",
        "documentDescribes": [
            image_package_id,
        ],
        "packages": [
            {
                "name": image_digest,
                "SPDXID": image_package_id,
                "downloadLocation": "NOASSERTION",
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": (
                            "pkg:oci/image@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                        ),
                    },
                ],
            },
            {
                "name": "github.com/example/widgets",
                "SPDXID": source_package_id,
                "downloadLocation": "https://github.com/example/widgets",
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": (
                            "pkg:golang/github.com/example/widgets@v1.0.0?type=module"
                        ),
                    },
                ],
            },
            {
                "name": "github.com/example/dependency",
                "SPDXID": "SPDXRef-Package-github.com.example.dependency-v1.0.0",
                "downloadLocation": "https://github.com/example/dependency",
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": (
                            "pkg:golang/github.com/example/dependency@v1.0.0"
                            "?type=module"
                        ),
                    },
                ],
            },
        ],
        "relationships": [
            {
                "spdxElementId": image_package_id,
                "relationshipType": "CONTAINS",
                "relatedSpdxElement": source_package_id,
            },
            {
                "spdxElementId": source_package_id,
                "relationshipType": "DEPENDS_ON",
                "relatedSpdxElement": (
                    "SPDXRef-Package-github.com.example.dependency-v1.0.0"
                ),
            },
        ],
    }


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

MOCK_APT_ARTIFACTS = [
    {
        "name": "projects/test-project/locations/us-east1/repositories/apt-repo/packages/curl/versions/7.88.1",
        "packageName": "curl",
        "createTime": "2024-01-06T00:00:00Z",
        "updateTime": "2024-01-06T00:00:00Z",
    },
]

MOCK_YUM_ARTIFACTS = [
    {
        "name": "projects/test-project/locations/us-east1/repositories/yum-repo/packages/bash/versions/5.2.26",
        "packageName": "bash",
        "createTime": "2024-01-07T00:00:00Z",
        "updateTime": "2024-01-07T00:00:00Z",
    },
]

# Transformed manifest data for the my-app image (matches MOCK_DOCKER_IMAGES[0])
MOCK_PLATFORM_IMAGES = [
    {
        "id": "sha256:def456",
        "digest": "sha256:def456",
        "type": "image",
        "architecture": "amd64",
        "os": "linux",
        "os_version": None,
        "os_features": None,
        "variant": None,
        "media_type": "application/vnd.oci.image.manifest.v1+json",
        "parent_digest": "sha256:abc123",
        "child_digest": "sha256:def456",
        "child_image_digests": ["sha256:def456"],
        "project_id": "test-project",
        "source_uri": None,
        "source_revision": None,
        "source_file": None,
        "layer_diff_ids": None,
    },
    {
        "id": "sha256:ghi789",
        "digest": "sha256:ghi789",
        "type": "image",
        "architecture": "arm64",
        "os": "linux",
        "os_version": None,
        "os_features": None,
        "variant": "v8",
        "media_type": "application/vnd.oci.image.manifest.v1+json",
        "parent_digest": "sha256:abc123",
        "child_digest": "sha256:ghi789",
        "child_image_digests": ["sha256:ghi789"],
        "project_id": "test-project",
        "source_uri": None,
        "source_revision": None,
        "source_file": None,
        "layer_diff_ids": None,
    },
]
