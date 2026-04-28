"""
Integration tests for ConditionalNodeLabel feature.

These tests verify that conditional labels are correctly applied to nodes
based on their property values during the load() operation.
"""

import pytest

from cartography.client.core.tx import load
from tests.data.graph.querybuilder.sample_data.conditional_label_data import (
    CONTAINER_IMAGES,
)
from tests.data.graph.querybuilder.sample_data.conditional_label_data import (
    CONTAINER_IMAGES_UPDATED,
)
from tests.data.graph.querybuilder.sample_data.conditional_label_data import (
    MERGE_CONTAINER_REGISTRY_QUERY,
)
from tests.data.graph.querybuilder.sample_data.conditional_label_data import (
    VULNERABILITIES,
)
from tests.data.graph.querybuilder.sample_models.conditional_label_models import (
    ContainerImageSchema,
)
from tests.data.graph.querybuilder.sample_models.conditional_label_models import (
    ContainerImageSchemaNoSubResource,
)
from tests.data.graph.querybuilder.sample_models.conditional_label_models import (
    VulnerabilitySchema,
)


@pytest.fixture(autouse=True)
def clear_graph(neo4j_session):
    """Clear the graph before each test to ensure test isolation."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    yield


def test_conditional_labels_applied_based_on_conditions(neo4j_session):
    """
    Test that conditional labels are applied to nodes based on their property values.

    This mimics the ECR use case where different image types get different ontology labels:
    - IMAGE -> Image label
    - IMAGE_ATTESTATION -> ImageAttestation label
    - IMAGE_MANIFEST_LIST -> ImageManifestList label
    """
    # Arrange: Create the container registry sub-resource
    neo4j_session.run(MERGE_CONTAINER_REGISTRY_QUERY)

    # Act: Load container images with conditional labels
    load(
        neo4j_session,
        ContainerImageSchema(),
        CONTAINER_IMAGES,
        lastupdated=1,
        REGISTRY_ID="registry-1",
    )

    # Assert: Verify unconditional "Resource" label is on all nodes
    result = neo4j_session.run(
        "MATCH (n:ContainerImage:Resource) RETURN count(n) AS count"
    )
    assert result.single()["count"] == 4

    # Assert: Verify "Image" label only on nodes with image_type="IMAGE"
    result = neo4j_session.run(
        "MATCH (n:ContainerImage:Image) RETURN n.id AS id ORDER BY n.id"
    )
    image_ids = [r["id"] for r in result]
    assert image_ids == ["sha256:abc123", "sha256:jkl012"]

    # Assert: Verify "ImageAttestation" label only on nodes with image_type="IMAGE_ATTESTATION"
    result = neo4j_session.run(
        "MATCH (n:ContainerImage:ImageAttestation) RETURN n.id AS id"
    )
    attestation_ids = [r["id"] for r in result]
    assert attestation_ids == ["sha256:def456"]

    # Assert: Verify "ImageManifestList" label only on nodes with image_type="IMAGE_MANIFEST_LIST"
    result = neo4j_session.run(
        "MATCH (n:ContainerImage:ImageManifestList) RETURN n.id AS id"
    )
    manifest_ids = [r["id"] for r in result]
    assert manifest_ids == ["sha256:ghi789"]


def test_conditional_labels_updated_when_conditions_change(neo4j_session):
    """
    Test that conditional labels are correctly updated when node properties change.

    When a node's property changes such that it no longer matches a condition,
    the label should be removed. When it matches a new condition, the new label
    should be applied.
    """
    # Arrange: Create the container registry and load initial data
    neo4j_session.run(MERGE_CONTAINER_REGISTRY_QUERY)
    load(
        neo4j_session,
        ContainerImageSchema(),
        CONTAINER_IMAGES[:2],  # Only first two images
        lastupdated=1,
        REGISTRY_ID="registry-1",
    )

    # Verify initial state
    result = neo4j_session.run("MATCH (n:ContainerImage:Image) RETURN n.id AS id")
    assert [r["id"] for r in result] == ["sha256:abc123"]

    result = neo4j_session.run(
        "MATCH (n:ContainerImage:ImageAttestation) RETURN n.id AS id"
    )
    assert [r["id"] for r in result] == ["sha256:def456"]

    # Act: Update the images with swapped types
    load(
        neo4j_session,
        ContainerImageSchema(),
        CONTAINER_IMAGES_UPDATED,
        lastupdated=2,
        REGISTRY_ID="registry-1",
    )

    # Assert: Labels should be swapped
    # sha256:abc123 was IMAGE, now IMAGE_ATTESTATION
    result = neo4j_session.run(
        "MATCH (n:ContainerImage{id: 'sha256:abc123'}) RETURN labels(n) AS labels"
    )
    labels = set(result.single()["labels"])
    assert "ImageAttestation" in labels
    assert "Image" not in labels

    # sha256:def456 was IMAGE_ATTESTATION, now IMAGE
    result = neo4j_session.run(
        "MATCH (n:ContainerImage{id: 'sha256:def456'}) RETURN labels(n) AS labels"
    )
    labels = set(result.single()["labels"])
    assert "Image" in labels
    assert "ImageAttestation" not in labels


def test_conditional_labels_with_multiple_conditions(neo4j_session):
    """
    Test that conditional labels with multiple conditions are only applied
    when ALL conditions are met (AND logic).
    """
    # Act: Load vulnerabilities
    load(
        neo4j_session,
        VulnerabilitySchema(),
        VULNERABILITIES,
        lastupdated=1,
    )

    # Assert: All vulnerabilities have the unconditional "SecurityFinding" label
    result = neo4j_session.run(
        "MATCH (n:Vulnerability:SecurityFinding) RETURN count(n) AS count"
    )
    assert result.single()["count"] == 4

    # Assert: "Critical" label only on severity="critical" nodes
    result = neo4j_session.run(
        "MATCH (n:Vulnerability:Critical) RETURN n.id AS id ORDER BY n.id"
    )
    critical_ids = [r["id"] for r in result]
    assert critical_ids == ["CVE-2024-0001", "CVE-2024-0002"]

    # Assert: "Urgent" label only on severity="critical" AND is_exploitable="true" nodes
    result = neo4j_session.run("MATCH (n:Vulnerability:Urgent) RETURN n.id AS id")
    urgent_ids = [r["id"] for r in result]
    assert urgent_ids == ["CVE-2024-0001"]

    # Assert: CVE-2024-0002 is Critical but NOT Urgent (is_exploitable="false")
    result = neo4j_session.run(
        "MATCH (n:Vulnerability{id: 'CVE-2024-0002'}) RETURN labels(n) AS labels"
    )
    labels = set(result.single()["labels"])
    assert "Critical" in labels
    assert "Urgent" not in labels


def test_conditional_labels_not_applied_when_conditions_not_met(neo4j_session):
    """
    Test that conditional labels are NOT applied when conditions are not met.
    """
    # Act: Load vulnerabilities
    load(
        neo4j_session,
        VulnerabilitySchema(),
        VULNERABILITIES,
        lastupdated=1,
    )

    # Assert: Low severity vulnerability has no Critical or Urgent labels
    result = neo4j_session.run(
        "MATCH (n:Vulnerability{id: 'CVE-2024-0004'}) RETURN labels(n) AS labels"
    )
    labels = set(result.single()["labels"])
    assert "Vulnerability" in labels
    assert "SecurityFinding" in labels  # Unconditional label
    assert "Critical" not in labels
    assert "Urgent" not in labels


def test_conditional_labels_scoped_to_sub_resource(neo4j_session):
    """
    Test that conditional labels are correctly scoped to the sub-resource.

    When using a schema with sub_resource_relationship, the conditional label
    queries should only affect nodes within the current sub-resource scope.
    """
    # Arrange: Create two container registries
    neo4j_session.run(
        "MERGE (r:ContainerRegistry{id: 'registry-1'}) SET r.lastupdated = 1"
    )
    neo4j_session.run(
        "MERGE (r:ContainerRegistry{id: 'registry-2'}) SET r.lastupdated = 1"
    )

    # Load images to registry-1
    load(
        neo4j_session,
        ContainerImageSchema(),
        [
            {
                "id": "img-1",
                "digest": "sha256:1",
                "image_type": "IMAGE",
                "repository": "app1",
            },
        ],
        lastupdated=1,
        REGISTRY_ID="registry-1",
    )

    # Load images to registry-2
    load(
        neo4j_session,
        ContainerImageSchema(),
        [
            {
                "id": "img-2",
                "digest": "sha256:2",
                "image_type": "IMAGE_ATTESTATION",
                "repository": "app2",
            },
        ],
        lastupdated=1,
        REGISTRY_ID="registry-2",
    )

    # Assert: img-1 has Image label (from registry-1)
    result = neo4j_session.run(
        "MATCH (n:ContainerImage{id: 'img-1'}) RETURN labels(n) AS labels"
    )
    labels = set(result.single()["labels"])
    assert "Image" in labels
    assert "ImageAttestation" not in labels

    # Assert: img-2 has ImageAttestation label (from registry-2)
    result = neo4j_session.run(
        "MATCH (n:ContainerImage{id: 'img-2'}) RETURN labels(n) AS labels"
    )
    labels = set(result.single()["labels"])
    assert "ImageAttestation" in labels
    assert "Image" not in labels

    # Now update only registry-1 with a new image type
    load(
        neo4j_session,
        ContainerImageSchema(),
        [
            {
                "id": "img-1",
                "digest": "sha256:1",
                "image_type": "IMAGE_ATTESTATION",
                "repository": "app1",
            },
        ],
        lastupdated=2,
        REGISTRY_ID="registry-1",
    )

    # Assert: img-1 label changed to ImageAttestation
    result = neo4j_session.run(
        "MATCH (n:ContainerImage{id: 'img-1'}) RETURN labels(n) AS labels"
    )
    labels = set(result.single()["labels"])
    assert "ImageAttestation" in labels
    assert "Image" not in labels

    # Assert: img-2 labels unchanged (different sub-resource)
    result = neo4j_session.run(
        "MATCH (n:ContainerImage{id: 'img-2'}) RETURN labels(n) AS labels"
    )
    labels = set(result.single()["labels"])
    assert "ImageAttestation" in labels


def test_conditional_labels_without_sub_resource(neo4j_session):
    """
    Test conditional labels on schemas without sub_resource_relationship (unscoped).
    """
    # Act: Load container images using unscoped schema
    load(
        neo4j_session,
        ContainerImageSchemaNoSubResource(),
        CONTAINER_IMAGES[:2],
        lastupdated=1,
    )

    # Assert: Labels are applied based on conditions
    result = neo4j_session.run("MATCH (n:ContainerImage:Image) RETURN n.id AS id")
    assert [r["id"] for r in result] == ["sha256:abc123"]

    result = neo4j_session.run(
        "MATCH (n:ContainerImage:ImageAttestation) RETURN n.id AS id"
    )
    assert [r["id"] for r in result] == ["sha256:def456"]


def test_all_labels_present_on_node(neo4j_session):
    """
    Test that a node has all expected labels: primary, unconditional extra, and conditional.
    """
    # Arrange: Create the container registry
    neo4j_session.run(MERGE_CONTAINER_REGISTRY_QUERY)

    # Act: Load a single image
    load(
        neo4j_session,
        ContainerImageSchema(),
        [
            {
                "id": "test-img",
                "digest": "sha256:test",
                "image_type": "IMAGE",
                "repository": "test",
            }
        ],
        lastupdated=1,
        REGISTRY_ID="registry-1",
    )

    # Assert: Node has all expected labels
    result = neo4j_session.run(
        "MATCH (n:ContainerImage{id: 'test-img'}) RETURN labels(n) AS labels"
    )
    labels = set(result.single()["labels"])

    # Primary label
    assert "ContainerImage" in labels
    # Unconditional extra label
    assert "Resource" in labels
    # Conditional label (matches image_type="IMAGE")
    assert "Image" in labels
    # Should NOT have other conditional labels
    assert "ImageAttestation" not in labels
    assert "ImageManifestList" not in labels
