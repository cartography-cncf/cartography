"""Test data for GitLab container registry module."""

TEST_ORG_URL = "https://gitlab.example.com/myorg"
TEST_GITLAB_URL = "https://gitlab.example.com"
TEST_REGISTRY_URL = "https://registry.gitlab.example.com"

# Raw GitLab API response for container repositories
# Matches /api/v4/groups/:id/registry/repositories response
GET_CONTAINER_REPOSITORIES_RESPONSE = [
    {
        "id": 1001,
        "name": "app",
        "path": "myorg/awesome-project/app",
        "project_id": 100,
        "location": "registry.gitlab.example.com/myorg/awesome-project/app",
        "created_at": "2024-01-15T10:00:00.000Z",
        "cleanup_policy_started_at": "2024-01-20T00:00:00.000Z",
        "tags_count": 3,
        "size": 524288000,
        "status": None,
    },
    {
        "id": 1002,
        "name": "worker",
        "path": "myorg/awesome-project/worker",
        "project_id": 100,
        "location": "registry.gitlab.example.com/myorg/awesome-project/worker",
        "created_at": "2024-01-16T11:00:00.000Z",
        "cleanup_policy_started_at": None,
        "tags_count": 2,
        "size": 268435456,
        "status": None,
    },
]

TRANSFORMED_CONTAINER_REPOSITORIES = [
    {
        "location": "registry.gitlab.example.com/myorg/awesome-project/app",
        "name": "app",
        "path": "myorg/awesome-project/app",
        "id": 1001,
        "project_id": 100,
        "created_at": "2024-01-15T10:00:00.000Z",
        "cleanup_policy_started_at": "2024-01-20T00:00:00.000Z",
        "tags_count": 3,
        "size": 524288000,
        "status": None,
    },
    {
        "location": "registry.gitlab.example.com/myorg/awesome-project/worker",
        "name": "worker",
        "path": "myorg/awesome-project/worker",
        "id": 1002,
        "project_id": 100,
        "created_at": "2024-01-16T11:00:00.000Z",
        "cleanup_policy_started_at": None,
        "tags_count": 2,
        "size": 268435456,
        "status": None,
    },
]

# Raw GitLab API response for container repository tags
# Matches /api/v4/projects/:id/registry/repositories/:repo_id/tags response
# Note: _repository_location is added by get_all_container_repository_tags
GET_CONTAINER_REPOSITORY_TAGS_RESPONSE = [
    {
        "name": "latest",
        "path": "myorg/awesome-project/app:latest",
        "location": "registry.gitlab.example.com/myorg/awesome-project/app:latest",
        "revision": "abc123def456abc123def456abc123def456abc1",
        "short_revision": "abc123de",
        "digest": "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        "created_at": "2024-01-20T15:30:00.000Z",
        "total_size": 104857600,
        "_repository_location": "registry.gitlab.example.com/myorg/awesome-project/app",
    },
    {
        "name": "v1.0.0",
        "path": "myorg/awesome-project/app:v1.0.0",
        "location": "registry.gitlab.example.com/myorg/awesome-project/app:v1.0.0",
        "revision": "def456ghi789def456ghi789def456ghi789def4",
        "short_revision": "def456gh",
        "digest": "sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444",
        "created_at": "2024-01-18T12:00:00.000Z",
        "total_size": 104857600,
        "_repository_location": "registry.gitlab.example.com/myorg/awesome-project/app",
    },
    {
        "name": "v0.9.0",
        "path": "myorg/awesome-project/worker:v0.9.0",
        "location": "registry.gitlab.example.com/myorg/awesome-project/worker:v0.9.0",
        "revision": "ghi789jkl012ghi789jkl012ghi789jkl012ghi7",
        "short_revision": "ghi789jk",
        "digest": "sha256:ccc333444555666777888999000aaabbbcccdddeeefff000111222333444555",
        "created_at": "2024-01-10T09:00:00.000Z",
        "total_size": 52428800,
        "_repository_location": "registry.gitlab.example.com/myorg/awesome-project/worker",
    },
]

TRANSFORMED_CONTAINER_REPOSITORY_TAGS = [
    {
        "location": "registry.gitlab.example.com/myorg/awesome-project/app:latest",
        "name": "latest",
        "path": "myorg/awesome-project/app:latest",
        "repository_location": "registry.gitlab.example.com/myorg/awesome-project/app",
        "revision": "abc123def456abc123def456abc123def456abc1",
        "short_revision": "abc123de",
        "digest": "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        "created_at": "2024-01-20T15:30:00.000Z",
        "total_size": 104857600,
    },
    {
        "location": "registry.gitlab.example.com/myorg/awesome-project/app:v1.0.0",
        "name": "v1.0.0",
        "path": "myorg/awesome-project/app:v1.0.0",
        "repository_location": "registry.gitlab.example.com/myorg/awesome-project/app",
        "revision": "def456ghi789def456ghi789def456ghi789def4",
        "short_revision": "def456gh",
        "digest": "sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444",
        "created_at": "2024-01-18T12:00:00.000Z",
        "total_size": 104857600,
    },
    {
        "location": "registry.gitlab.example.com/myorg/awesome-project/worker:v0.9.0",
        "name": "v0.9.0",
        "path": "myorg/awesome-project/worker:v0.9.0",
        "repository_location": "registry.gitlab.example.com/myorg/awesome-project/worker",
        "revision": "ghi789jkl012ghi789jkl012ghi789jkl012ghi7",
        "short_revision": "ghi789jk",
        "digest": "sha256:ccc333444555666777888999000aaabbbcccdddeeefff000111222333444555",
        "created_at": "2024-01-10T09:00:00.000Z",
        "total_size": 52428800,
    },
]

# Raw manifest data from Docker Registry V2 API with metadata added by get_container_images
# Includes both regular images and manifest lists (manifest lists also returned separately for attestation discovery)
GET_CONTAINER_IMAGES_RESPONSE = [
    # Regular image (linux/amd64)
    {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": 7023,
            "digest": "sha256:config111222333444555666777888999000aaabbbcccdddeeefff000111222",
        },
        "layers": [
            {
                "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                "size": 32654,
                "digest": "sha256:layer1111222333444555666777888999000aaabbbcccdddeeefff00011122",
            },
        ],
        "_digest": "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        "_repository_name": "myorg/awesome-project/app",
        "_registry_url": TEST_REGISTRY_URL,
        "_reference": "latest",
        "_config": {
            "architecture": "amd64",
            "os": "linux",
            "variant": None,
        },
    },
    # Multi-arch manifest list
    {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
        "manifests": [
            {
                "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                "size": 7143,
                "digest": "sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444",
                "platform": {
                    "architecture": "amd64",
                    "os": "linux",
                },
            },
            {
                "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                "size": 7143,
                "digest": "sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444",
                "platform": {
                    "architecture": "arm64",
                    "os": "linux",
                    "variant": "v8",
                },
            },
        ],
        "_digest": "sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444",
        "_repository_name": "myorg/awesome-project/app",
        "_registry_url": TEST_REGISTRY_URL,
        "_reference": "v1.0.0",
    },
    # Child image 1 (linux/amd64) - from manifest list
    {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": 7023,
            "digest": "sha256:configchild1222333444555666777888999000aaabbbcccdddeeefff000111",
        },
        "layers": [],
        "_digest": "sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444",
        "_repository_name": "myorg/awesome-project/app",
        "_registry_url": TEST_REGISTRY_URL,
        "_reference": "sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444",
        "_config": {
            "architecture": "amd64",
            "os": "linux",
            "variant": None,
        },
    },
    # Child image 2 (linux/arm64) - from manifest list
    {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": 7023,
            "digest": "sha256:configchild2222333444555666777888999000aaabbbcccdddeeefff000111",
        },
        "layers": [],
        "_digest": "sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444",
        "_repository_name": "myorg/awesome-project/app",
        "_registry_url": TEST_REGISTRY_URL,
        "_reference": "sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444",
        "_config": {
            "architecture": "arm64",
            "os": "linux",
            "variant": "v8",
        },
    },
    # Regular image for worker
    {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": 5012,
            "digest": "sha256:configworker222333444555666777888999000aaabbbcccdddeeefff000111",
        },
        "layers": [],
        "_digest": "sha256:ccc333444555666777888999000aaabbbcccdddeeefff000111222333444555",
        "_repository_name": "myorg/awesome-project/worker",
        "_registry_url": TEST_REGISTRY_URL,
        "_reference": "v0.9.0",
        "_config": {
            "architecture": "amd64",
            "os": "linux",
            "variant": None,
        },
    },
]

# Manifest lists returned separately for buildx attestation discovery
GET_CONTAINER_MANIFEST_LISTS_RESPONSE = [
    # Multi-arch manifest list with child images
    {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
        "manifests": [
            {
                "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                "size": 7143,
                "digest": "sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444",
                "platform": {
                    "architecture": "amd64",
                    "os": "linux",
                },
            },
            {
                "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                "size": 7143,
                "digest": "sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444",
                "platform": {
                    "architecture": "arm64",
                    "os": "linux",
                    "variant": "v8",
                },
            },
        ],
        "_digest": "sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444",
        "_repository_name": "myorg/awesome-project/app",
        "_registry_url": TEST_REGISTRY_URL,
        "_reference": "v1.0.0",
    },
]

TRANSFORMED_CONTAINER_IMAGES = [
    {
        "digest": "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        "uri": "registry.gitlab.example.com/myorg/awesome-project/app",
        "media_type": "application/vnd.docker.distribution.manifest.v2+json",
        "schema_version": 2,
        "type": "image",
        "architecture": "amd64",
        "os": "linux",
        "variant": None,
        "child_image_digests": None,
    },
    {
        "digest": "sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444",
        "uri": "registry.gitlab.example.com/myorg/awesome-project/app",
        "media_type": "application/vnd.docker.distribution.manifest.list.v2+json",
        "schema_version": 2,
        "type": "manifest_list",
        "architecture": None,
        "os": None,
        "variant": None,
        "child_image_digests": [
            "sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444",
            "sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444",
        ],
    },
    {
        "digest": "sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444",
        "uri": "registry.gitlab.example.com/myorg/awesome-project/app",
        "media_type": "application/vnd.docker.distribution.manifest.v2+json",
        "schema_version": 2,
        "type": "image",
        "architecture": "amd64",
        "os": "linux",
        "variant": None,
        "child_image_digests": None,
    },
    {
        "digest": "sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444",
        "uri": "registry.gitlab.example.com/myorg/awesome-project/app",
        "media_type": "application/vnd.docker.distribution.manifest.v2+json",
        "schema_version": 2,
        "type": "image",
        "architecture": "arm64",
        "os": "linux",
        "variant": "v8",
        "child_image_digests": None,
    },
    {
        "digest": "sha256:ccc333444555666777888999000aaabbbcccdddeeefff000111222333444555",
        "uri": "registry.gitlab.example.com/myorg/awesome-project/worker",
        "media_type": "application/vnd.docker.distribution.manifest.v2+json",
        "schema_version": 2,
        "type": "image",
        "architecture": "amd64",
        "os": "linux",
        "variant": None,
        "child_image_digests": None,
    },
]

# Raw attestation data from Registry V2 API with metadata added by get_container_image_attestations
# Only the "latest" image has attestations (signature and attestation)
GET_CONTAINER_IMAGE_ATTESTATIONS_RESPONSE = [
    # Signature for latest image
    {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {
            "mediaType": "application/vnd.dev.cosign.simplesigning.v1+json",
            "size": 233,
            "digest": "sha256:sigconfig111222333444555666777888999000aaabbbcccdddeeefff00011",
        },
        "layers": [
            {
                "mediaType": "application/vnd.dev.cosign.simplesigning.v1+json",
                "size": 345,
                "digest": "sha256:siglayer111222333444555666777888999000aaabbbcccdddeeefff000111",
            },
        ],
        "_digest": "sha256:sig111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        "_registry_url": TEST_REGISTRY_URL,
        "_repository_name": "myorg/awesome-project/app",
        "_attests_digest": "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        "_attestation_type": "sig",
    },
    # Attestation (SLSA provenance) for latest image
    {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {
            "mediaType": "application/vnd.dsse.envelope.v1+json",
            "size": 233,
            "digest": "sha256:attconfig111222333444555666777888999000aaabbbcccdddeeefff00011",
        },
        "layers": [
            {
                "mediaType": "application/vnd.dsse.envelope.v1+json",
                "size": 1234,
                "digest": "sha256:attlayer111222333444555666777888999000aaabbbcccdddeeefff000111",
            },
        ],
        "predicateType": "https://slsa.dev/provenance/v0.2",
        "_digest": "sha256:att111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        "_registry_url": TEST_REGISTRY_URL,
        "_repository_name": "myorg/awesome-project/app",
        "_attests_digest": "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        "_attestation_type": "att",
    },
]

TRANSFORMED_CONTAINER_IMAGE_ATTESTATIONS = [
    {
        "digest": "sha256:sig111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        "media_type": "application/vnd.oci.image.manifest.v1+json",
        "attestation_type": "sig",
        "predicate_type": None,
        "attests_digest": "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
    },
    {
        "digest": "sha256:att111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        "media_type": "application/vnd.oci.image.manifest.v1+json",
        "attestation_type": "att",
        "predicate_type": "https://slsa.dev/provenance/v0.2",
        "attests_digest": "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
    },
]
