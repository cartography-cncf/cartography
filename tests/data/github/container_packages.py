"""
Test data for GitHub Container Packages.
"""

GET_CONTAINER_PACKAGES = [
    {
        "id": 123456,
        "name": "my-app",
        "package_type": "container",
        "visibility": "public",
        "url": "https://api.github.com/orgs/test-org/packages/container/my-app",
        "html_url": "https://github.com/orgs/test-org/packages/container/my-app",
        "owner": {"login": "test-org", "type": "Organization"},
        "repository": {"id": 456789, "full_name": "test-org/my-app-repo"},
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-02T00:00:00Z",
    }
]

GET_PACKAGE_VERSIONS = [
    {
        "id": 987654,
        "name": "sha256:digest123", # GHCR uses digest as version name
        "url": "https://api.github.com/orgs/test-org/packages/container/my-app/versions/987654",
        "html_url": "https://github.com/orgs/test-org/packages/container/my-app/versions/sha256:digest123",
        "metadata": {
            "container": {
                "tags": ["latest", "v1.0.0"]
            }
        },
        "created_at": "2023-01-02T00:00:00Z",
        "updated_at": "2023-01-02T00:00:00Z",
    }
]

# Mock manifest for a regular image
IMAGE_MANIFEST = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
    "config": {
        "mediaType": "application/vnd.docker.container.image.v1+json",
        "size": 7023,
        "digest": "sha256:config123"
    },
    "layers": [
        {"mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip", "size": 3262, "digest": "sha256:layer1"}
    ]
}

# Mock config blob
IMAGE_CONFIG = {
    "architecture": "amd64",
    "os": "linux",
    "variant": None
}

# Mock manifest list (multi-arch)
MANIFEST_LIST = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
    "manifests": [
        {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "size": 528,
            "digest": "sha256:child_amd64",
            "platform": {"architecture": "amd64", "os": "linux"}
        },
        {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "size": 528,
            "digest": "sha256:child_arm64",
            "platform": {"architecture": "arm64", "os": "linux"}
        }
    ]
}
