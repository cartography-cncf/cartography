"""
Integration tests for docker buildx imagetools with real-world output.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from neo4j import Session

from cartography.intel.trivy.image_lineage import build_image_layers
from cartography.intel.trivy.image_lineage import compute_ecr_image_lineage
from cartography.intel.trivy.layers import get_image_layers_from_registry
from cartography.intel.trivy.layers import get_image_platforms

TEST_DATA_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "trivy"


def load_test_data(filename: str) -> dict:
    """Load test data from the data directory."""
    with open(TEST_DATA_DIR / filename) as f:
        return json.load(f)


@patch("cartography.intel.trivy.layers.subprocess.run")
@patch("cartography.intel.trivy.layers.check_docker_buildx_available")
def test_get_platforms_filters_attestations(mock_check_docker, mock_run):
    """Test that attestation manifests are properly filtered from platform list."""
    mock_check_docker.return_value = True

    # Load real docker buildx manifest output
    manifest_data = load_test_data("docker_buildx_manifest.json")
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(manifest_data),
    )

    # Get platforms - should filter out attestation manifests
    platforms = get_image_platforms(
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/test-app:v1.0.0"
    )

    # Should only have the real platforms, not the attestation manifests
    assert len(platforms) == 2
    assert "linux/amd64" in platforms
    assert "linux/arm64" in platforms
    # Should not include unknown/unknown platforms from attestations
    assert "unknown/unknown" not in platforms

    # Verify all returned platforms are valid
    for platform in platforms:
        assert "/" in platform
        parts = platform.split("/")
        assert parts[0] in ["linux", "darwin", "windows"]
        assert parts[1] in ["amd64", "arm64", "arm", "386", "ppc64le", "s390x"]


@patch("cartography.intel.trivy.layers.subprocess.run")
@patch("cartography.intel.trivy.layers.check_docker_buildx_available")
@patch("cartography.intel.trivy.layers.get_registry_auth_for_ecr")
def test_get_layers_extracts_diff_ids(mock_auth, mock_check_docker, mock_run):
    """Test that layer extraction properly gets diff IDs and image digest."""
    mock_check_docker.return_value = True
    mock_auth.return_value = True

    # Load real docker buildx image output
    image_data = load_test_data("docker_buildx_image.json")
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(image_data),
    )

    # Get layers for the image
    diff_ids, digest = get_image_layers_from_registry(
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/test-app:v1.0.0",
        platform="linux/amd64",
    )

    # Verify we got all 15 layers
    assert diff_ids is not None
    assert len(diff_ids) == 15

    # Verify layer format - all should be sha256 hashes
    for layer_id in diff_ids:
        assert layer_id.startswith("sha256:")
        # sha256: prefix (7 chars) + hex digest
        assert len(layer_id) > 7
        # Verify it's a valid hex string after the prefix
        hex_part = layer_id[7:]
        assert all(c in "0123456789abcdef" for c in hex_part)

    # Verify we got the config digest
    assert (
        digest
        == "sha256:config11111111111111111111111111111111111111111111111111111111"
    )

    # Verify the exact layer order is preserved
    expected_first = (
        "sha256:aaaa1111222233334444555566667777888899990000aaaabbbbccccddddeee1"
    )
    expected_last = (
        "sha256:fff0000000000000000000000000000000000000000000000000000000000000"
    )
    assert diff_ids[0] == expected_first
    assert diff_ids[-1] == expected_last


@patch("cartography.intel.trivy.layers.subprocess.run")
@patch("cartography.intel.trivy.layers.check_docker_buildx_available")
@patch("cartography.intel.trivy.layers.get_registry_auth_for_ecr")
def test_build_layers_creates_graph_structure(
    mock_auth, mock_check_docker, mock_run, neo4j_session: Session
):
    """Test that build_image_layers creates correct graph structure with layers."""
    # Clean up any existing data
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    mock_check_docker.return_value = True
    mock_auth.return_value = True

    # Load real docker buildx image output
    image_data = load_test_data("docker_buildx_image.json")
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(image_data),
    )

    # Create the ECRImage node
    image_digest = (
        "sha256:testdigest111111111111111111111111111111111111111111111111111"
    )
    neo4j_session.run(
        "MERGE (:ECRImage {id: $id})",
        id=image_digest,
    )

    # Build layers from registry
    layers = build_image_layers(
        neo4j_session,
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/test-app:v1.0.0",
        image_digest,
        "linux/amd64",
        123456789,
    )

    # Verify layers were returned
    assert layers is not None
    assert len(layers) == 15

    # Verify all layers were created in Neo4j
    layer_count = neo4j_session.run(
        "MATCH (l:ImageLayer) RETURN count(l) as count"
    ).single()["count"]
    assert layer_count == 15

    # Verify each layer has the correct properties
    for layer_id in layers:
        result = neo4j_session.run(
            "MATCH (l:ImageLayer {diff_id: $diff_id}) RETURN l",
            diff_id=layer_id,
        ).single()
        assert result is not None
        layer_node = result["l"]
        assert layer_node["diff_id"] == layer_id
        assert layer_node["lastupdated"] == 123456789

    # Verify HEAD relationship points to first layer
    head_result = neo4j_session.run(
        """
        MATCH (i:ECRImage {id: $id})-[:HEAD]->(h:ImageLayer)
        RETURN h.diff_id as head_id
        """,
        id=image_digest,
    ).single()
    assert head_result["head_id"] == layers[0]

    # Verify TAIL relationship points to last layer
    tail_result = neo4j_session.run(
        """
        MATCH (i:ECRImage {id: $id})-[:TAIL]->(t:ImageLayer)
        RETURN t.diff_id as tail_id
        """,
        id=image_digest,
    ).single()
    assert tail_result["tail_id"] == layers[-1]

    # Verify NEXT relationships form a chain
    chain_result = neo4j_session.run(
        """
        MATCH path = (h:ImageLayer)-[:NEXT*]->(t:ImageLayer)
        WHERE NOT ()-[:NEXT]->(h) AND NOT (t)-[:NEXT]->()
        RETURN length(path) as chain_length
        """
    ).single()
    assert chain_result["chain_length"] == 14  # 15 nodes = 14 edges

    # Verify image has correct length property
    image_result = neo4j_session.run(
        "MATCH (i:ECRImage {id: $id}) RETURN i.length as length",
        id=image_digest,
    ).single()
    assert image_result["length"] == 15


@patch("cartography.intel.trivy.layers.subprocess.run")
@patch("cartography.intel.trivy.layers.check_docker_buildx_available")
@patch("cartography.intel.trivy.layers.get_registry_auth_for_ecr")
def test_lineage_detection_with_shared_layers(
    mock_auth, mock_check_docker, mock_run, neo4j_session: Session
):
    """Test that lineage is correctly detected when images share layer prefixes."""
    # Clean up any existing data
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    mock_check_docker.return_value = True
    mock_auth.return_value = True

    # Base image layers (subset of the full image)
    base_layers = load_test_data("docker_buildx_image.json")
    base_layers["Image"]["RootFS"]["DiffIDs"] = base_layers["Image"]["RootFS"][
        "DiffIDs"
    ][:10]
    base_digest = "sha256:basedigest11111111111111111111111111111111111111111111111111"

    # Child image layers (all layers from base + additional)
    child_layers = load_test_data("docker_buildx_image.json")
    child_digest = "sha256:childdigest1111111111111111111111111111111111111111111111111"

    # Create ECRImage nodes
    neo4j_session.run(
        """
        MERGE (:ECRImage {id: $base_id, uri: $base_uri})
        MERGE (:ECRImage {id: $child_id, uri: $child_uri})
        """,
        base_id=base_digest,
        base_uri="123456789012.dkr.ecr.us-east-1.amazonaws.com/base-app:v1.0.0",
        child_id=child_digest,
        child_uri="123456789012.dkr.ecr.us-east-1.amazonaws.com/child-app:v2.0.0",
    )

    # Mock base image layers
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(base_layers),
    )

    # Build base image layers
    base_layer_ids = build_image_layers(
        neo4j_session,
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/base-app:v1.0.0",
        base_digest,
        "linux/amd64",
        123456789,
    )

    assert base_layer_ids is not None  # Type check for mypy
    assert len(base_layer_ids) == 10

    # Mock child image layers
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(child_layers),
    )

    # Build child image layers
    child_layer_ids = build_image_layers(
        neo4j_session,
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/child-app:v2.0.0",
        child_digest,
        "linux/amd64",
        123456789,
    )

    assert child_layer_ids is not None  # Type check for mypy
    assert len(child_layer_ids) == 15

    # Verify layers are shared (child contains all base layers as prefix)
    assert child_layer_ids[:10] == base_layer_ids

    # Compute lineage relationships
    compute_ecr_image_lineage(neo4j_session)

    # Verify BUILT_FROM relationship was created
    lineage_result = neo4j_session.run(
        """
        MATCH (child:ECRImage {id: $child_id})-[:BUILT_FROM]->(base:ECRImage {id: $base_id})
        RETURN count(*) as count
        """,
        child_id=child_digest,
        base_id=base_digest,
    ).single()
    assert lineage_result["count"] == 1

    # Verify no self-relationships
    self_rel = neo4j_session.run(
        """
        MATCH (i:ECRImage)-[:BUILT_FROM]->(i)
        RETURN count(*) as count
        """
    ).single()
    assert self_rel["count"] == 0

    # Verify total unique layers (should be 15, not 25, due to sharing)
    total_layers = neo4j_session.run(
        "MATCH (l:ImageLayer) RETURN count(DISTINCT l) as count"
    ).single()["count"]
    assert total_layers == 15
