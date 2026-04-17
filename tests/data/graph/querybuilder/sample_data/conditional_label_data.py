# Sample data for conditional label integration tests

# Container images with different types - mimics ECR use case
CONTAINER_IMAGES = [
    {
        "id": "sha256:abc123",
        "digest": "sha256:abc123",
        "image_type": "IMAGE",
        "repository": "my-app",
    },
    {
        "id": "sha256:def456",
        "digest": "sha256:def456",
        "image_type": "IMAGE_ATTESTATION",
        "repository": "my-app",
    },
    {
        "id": "sha256:ghi789",
        "digest": "sha256:ghi789",
        "image_type": "IMAGE_MANIFEST_LIST",
        "repository": "my-app",
    },
    {
        "id": "sha256:jkl012",
        "digest": "sha256:jkl012",
        "image_type": "IMAGE",
        "repository": "other-app",
    },
]

# Container images for update test - same IDs but different types
CONTAINER_IMAGES_UPDATED = [
    {
        "id": "sha256:abc123",
        "digest": "sha256:abc123",
        "image_type": "IMAGE_ATTESTATION",  # Changed from IMAGE
        "repository": "my-app",
    },
    {
        "id": "sha256:def456",
        "digest": "sha256:def456",
        "image_type": "IMAGE",  # Changed from IMAGE_ATTESTATION
        "repository": "my-app",
    },
]

# Vulnerabilities for multi-condition tests
VULNERABILITIES = [
    {
        "id": "CVE-2024-0001",
        "severity": "critical",
        "is_exploitable": "true",
        "has_fix": "true",
    },
    {
        "id": "CVE-2024-0002",
        "severity": "critical",
        "is_exploitable": "false",
        "has_fix": "false",
    },
    {
        "id": "CVE-2024-0003",
        "severity": "high",
        "is_exploitable": "true",
        "has_fix": "true",
    },
    {
        "id": "CVE-2024-0004",
        "severity": "low",
        "is_exploitable": "false",
        "has_fix": "false",
    },
]

# Cypher query to create a container registry for sub-resource tests
MERGE_CONTAINER_REGISTRY_QUERY = """
MERGE (r:ContainerRegistry{id: 'registry-1'})
ON CREATE SET r.firstseen = timestamp()
SET r.lastupdated = 1
"""
