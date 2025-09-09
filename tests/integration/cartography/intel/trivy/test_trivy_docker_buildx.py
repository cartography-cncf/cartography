"""
Integration tests for docker buildx imagetools with real-world output.
"""

import copy
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
TEST_UPDATE_TAG = 123456789


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
def test_get_layers_multiplatform_image(mock_auth, mock_check_docker, mock_run):
    """Test layer extraction from real multi-platform image with platform-keyed Image field."""
    mock_check_docker.return_value = True
    mock_auth.return_value = True

    # Load real multi-platform docker buildx output
    multiplatform_data = load_test_data("docker_buildx_multiplatform_image.json")
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(multiplatform_data),
    )

    # Get layers for linux/amd64 platform (default)
    diff_ids = get_image_layers_from_registry(
        "482544513907.dkr.ecr.us-east-1.amazonaws.com/subimage-shared:0.0.3",
        platform="linux/amd64",
    )

    # Verify we got the amd64 layers
    assert diff_ids is not None
    assert len(diff_ids) == 10
    assert (
        diff_ids[0]
        == "sha256:ea680fbff095473bb8a6c867938d6d851e11ef0c177fce983ccc83440172bd72"
    )
    assert (
        diff_ids[-1]
        == "sha256:6cf50a16bdb06e023fd86430f364ca0f186157a69abecdd4ea99cd2fbca80db8"
    )

    # Test that we always get linux/amd64 by default (no arm64 for now)
    diff_ids_default = get_image_layers_from_registry(
        "482544513907.dkr.ecr.us-east-1.amazonaws.com/subimage-shared:0.0.3",
    )

    # Should get the same amd64 layers by default
    assert diff_ids_default == diff_ids


@patch("cartography.intel.trivy.layers.subprocess.run")
@patch("cartography.intel.trivy.layers.check_docker_buildx_available")
@patch("cartography.intel.trivy.layers.get_registry_auth_for_ecr")
def test_lineage_detection_basic_parent_child(
    mock_auth, mock_check_docker, mock_run, neo4j_session: Session
):
    """Test basic parent-child lineage detection when child extends parent layers."""
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
        TEST_UPDATE_TAG,
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
        TEST_UPDATE_TAG,
    )

    assert child_layer_ids is not None  # Type check for mypy
    assert len(child_layer_ids) == 15

    # Verify layers are shared (child contains all base layers as prefix)
    assert child_layer_ids[:10] == base_layer_ids

    # Compute lineage relationships
    compute_ecr_image_lineage(neo4j_session, TEST_UPDATE_TAG)

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


@patch("cartography.intel.trivy.layers.subprocess.run")
@patch("cartography.intel.trivy.layers.check_docker_buildx_available")
@patch("cartography.intel.trivy.layers.get_registry_auth_for_ecr")
def test_lineage_detection_multi_generation(
    mock_auth, mock_check_docker, mock_run, neo4j_session: Session
):
    """Test multi-generation lineage: grandparent -> parent -> child."""
    # Clean up any existing data
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    mock_check_docker.return_value = True
    mock_auth.return_value = True

    base_data = load_test_data("docker_buildx_image.json")

    # Grandparent: 5 layers
    grandparent_layers = copy.deepcopy(base_data)
    grandparent_layers["Image"]["RootFS"]["DiffIDs"] = base_data["Image"]["RootFS"][
        "DiffIDs"
    ][:5]
    grandparent_digest = (
        "sha256:grand11111111111111111111111111111111111111111111111111111111"
    )

    # Parent: 10 layers (extends grandparent)
    parent_layers = copy.deepcopy(base_data)
    parent_layers["Image"]["RootFS"]["DiffIDs"] = base_data["Image"]["RootFS"][
        "DiffIDs"
    ][:10]
    parent_digest = (
        "sha256:parent1111111111111111111111111111111111111111111111111111111"
    )

    # Child: 15 layers (extends parent)
    child_layers = base_data
    child_digest = (
        "sha256:child11111111111111111111111111111111111111111111111111111111"
    )

    # Create ECRImage nodes
    neo4j_session.run(
        """
        MERGE (:ECRImage {id: $grand_id, uri: 'ecr.com/grand:v1'})
        MERGE (:ECRImage {id: $parent_id, uri: 'ecr.com/parent:v2'})
        MERGE (:ECRImage {id: $child_id, uri: 'ecr.com/child:v3'})
        """,
        grand_id=grandparent_digest,
        parent_id=parent_digest,
        child_id=child_digest,
    )

    # Build layers for all three images
    for digest, layers, uri in [
        (grandparent_digest, grandparent_layers, "ecr.com/grand:v1"),
        (parent_digest, parent_layers, "ecr.com/parent:v2"),
        (child_digest, child_layers, "ecr.com/child:v3"),
    ]:
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(layers))
        build_image_layers(neo4j_session, uri, digest, TEST_UPDATE_TAG)

    # Compute lineage
    compute_ecr_image_lineage(neo4j_session, TEST_UPDATE_TAG)

    # Verify child -> parent relationship
    child_parent = neo4j_session.run(
        """
        MATCH (child:ECRImage {id: $child_id})-[:BUILT_FROM]->(parent:ECRImage {id: $parent_id})
        RETURN count(*) as count
        """,
        child_id=child_digest,
        parent_id=parent_digest,
    ).single()
    assert child_parent["count"] == 1

    # Verify parent -> grandparent relationship
    parent_grand = neo4j_session.run(
        """
        MATCH (parent:ECRImage {id: $parent_id})-[:BUILT_FROM]->(grand:ECRImage {id: $grand_id})
        RETURN count(*) as count
        """,
        parent_id=parent_digest,
        grand_id=grandparent_digest,
    ).single()
    assert parent_grand["count"] == 1

    # Verify NO direct child -> grandparent relationship (only immediate parent)
    child_grand = neo4j_session.run(
        """
        MATCH (child:ECRImage {id: $child_id})-[:BUILT_FROM]->(grand:ECRImage {id: $grand_id})
        RETURN count(*) as count
        """,
        child_id=child_digest,
        grand_id=grandparent_digest,
    ).single()
    assert child_grand["count"] == 0  # Should only link to immediate parent

    # Verify we can traverse the full lineage
    full_lineage = neo4j_session.run(
        """
        MATCH path = (child:ECRImage {id: $child_id})-[:BUILT_FROM*]->(ancestor:ECRImage)
        RETURN count(ancestor) as ancestors
        """,
        child_id=child_digest,
    ).single()
    assert full_lineage["ancestors"] == 2  # Parent and grandparent


@patch("cartography.intel.trivy.layers.subprocess.run")
@patch("cartography.intel.trivy.layers.check_docker_buildx_available")
@patch("cartography.intel.trivy.layers.get_registry_auth_for_ecr")
def test_lineage_detection_unrelated_images(
    mock_auth, mock_check_docker, mock_run, neo4j_session: Session
):
    """Test that unrelated images don't get linked."""
    # Clean up any existing data
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    mock_check_docker.return_value = True
    mock_auth.return_value = True

    base_data = load_test_data("docker_buildx_image.json")

    # Image A: layers 0-9
    image_a_layers = copy.deepcopy(base_data)
    image_a_layers["Image"]["RootFS"]["DiffIDs"] = base_data["Image"]["RootFS"][
        "DiffIDs"
    ][:10]
    image_a_digest = (
        "sha256:aaaa11111111111111111111111111111111111111111111111111111111"
    )

    # Image B: layers 5-14 (overlaps with A but doesn't start with same layers)
    image_b_layers = copy.deepcopy(base_data)
    image_b_layers["Image"]["RootFS"]["DiffIDs"] = base_data["Image"]["RootFS"][
        "DiffIDs"
    ][5:15]
    image_b_digest = (
        "sha256:bbbb11111111111111111111111111111111111111111111111111111111"
    )

    # Image C: completely different layers
    image_c_layers = copy.deepcopy(base_data)
    image_c_layers["Image"]["RootFS"]["DiffIDs"] = [
        "sha256:different111111111111111111111111111111111111111111111111111111",
        "sha256:different222222222222222222222222222222222222222222222222222222",
        "sha256:different333333333333333333333333333333333333333333333333333333",
    ]
    image_c_digest = (
        "sha256:cccc11111111111111111111111111111111111111111111111111111111"
    )

    # Create ECRImage nodes
    neo4j_session.run(
        """
        MERGE (:ECRImage {id: $a_id, uri: 'ecr.com/a:v1'})
        MERGE (:ECRImage {id: $b_id, uri: 'ecr.com/b:v1'})
        MERGE (:ECRImage {id: $c_id, uri: 'ecr.com/c:v1'})
        """,
        a_id=image_a_digest,
        b_id=image_b_digest,
        c_id=image_c_digest,
    )

    # Build layers for all images
    for digest, layers, uri in [
        (image_a_digest, image_a_layers, "ecr.com/a:v1"),
        (image_b_digest, image_b_layers, "ecr.com/b:v1"),
        (image_c_digest, image_c_layers, "ecr.com/c:v1"),
    ]:
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(layers))
        build_image_layers(neo4j_session, uri, digest, TEST_UPDATE_TAG)

    # Compute lineage
    compute_ecr_image_lineage(neo4j_session, TEST_UPDATE_TAG)

    # Verify NO relationships were created (none are parent-child)
    relationships = neo4j_session.run(
        """
        MATCH (:ECRImage)-[r:BUILT_FROM]->(:ECRImage)
        RETURN count(r) as count
        """
    ).single()
    assert relationships["count"] == 0


@patch("cartography.intel.trivy.layers.subprocess.run")
@patch("cartography.intel.trivy.layers.check_docker_buildx_available")
@patch("cartography.intel.trivy.layers.get_registry_auth_for_ecr")
def test_lineage_detection_multiple_children(
    mock_auth, mock_check_docker, mock_run, neo4j_session: Session
):
    """Test that multiple images can be built from the same base."""
    # Clean up any existing data
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    mock_check_docker.return_value = True
    mock_auth.return_value = True

    base_data = load_test_data("docker_buildx_image.json")

    # Base image: 8 layers
    base_layers = copy.deepcopy(base_data)
    base_layers["Image"]["RootFS"]["DiffIDs"] = base_data["Image"]["RootFS"]["DiffIDs"][
        :8
    ]
    base_digest = "sha256:base11111111111111111111111111111111111111111111111111111111"

    # Child A: base + 2 additional layers
    child_a_layers = copy.deepcopy(base_data)
    child_a_layers["Image"]["RootFS"]["DiffIDs"] = base_data["Image"]["RootFS"][
        "DiffIDs"
    ][:10]
    child_a_digest = (
        "sha256:childa111111111111111111111111111111111111111111111111111111"
    )

    # Child B: base + 4 additional layers (different from A)
    child_b_layers = copy.deepcopy(base_data)
    child_b_layers["Image"]["RootFS"]["DiffIDs"] = base_data["Image"]["RootFS"][
        "DiffIDs"
    ][:8] + [
        "sha256:childb111111111111111111111111111111111111111111111111111111",
        "sha256:childb222222222222222222222222222222222222222222222222222222",
        "sha256:childb333333333333333333333333333333333333333333333333333333",
        "sha256:childb444444444444444444444444444444444444444444444444444444",
    ]
    child_b_digest = (
        "sha256:childb111111111111111111111111111111111111111111111111111111"
    )

    # Create ECRImage nodes
    neo4j_session.run(
        """
        MERGE (:ECRImage {id: $base_id, uri: 'ecr.com/base:v1'})
        MERGE (:ECRImage {id: $child_a_id, uri: 'ecr.com/child-a:v1'})
        MERGE (:ECRImage {id: $child_b_id, uri: 'ecr.com/child-b:v1'})
        """,
        base_id=base_digest,
        child_a_id=child_a_digest,
        child_b_id=child_b_digest,
    )

    # Build layers for all images
    for digest, layers, uri in [
        (base_digest, base_layers, "ecr.com/base:v1"),
        (child_a_digest, child_a_layers, "ecr.com/child-a:v1"),
        (child_b_digest, child_b_layers, "ecr.com/child-b:v1"),
    ]:
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(layers))
        build_image_layers(neo4j_session, uri, digest, TEST_UPDATE_TAG)

    # Compute lineage
    compute_ecr_image_lineage(neo4j_session, TEST_UPDATE_TAG)

    # Verify both children are linked to base
    child_a_rel = neo4j_session.run(
        """
        MATCH (child:ECRImage {id: $child_id})-[:BUILT_FROM]->(base:ECRImage {id: $base_id})
        RETURN count(*) as count
        """,
        child_id=child_a_digest,
        base_id=base_digest,
    ).single()
    assert child_a_rel["count"] == 1

    child_b_rel = neo4j_session.run(
        """
        MATCH (child:ECRImage {id: $child_id})-[:BUILT_FROM]->(base:ECRImage {id: $base_id})
        RETURN count(*) as count
        """,
        child_id=child_b_digest,
        base_id=base_digest,
    ).single()
    assert child_b_rel["count"] == 1

    # Verify children are NOT linked to each other
    sibling_rel = neo4j_session.run(
        """
        MATCH (a:ECRImage {id: $a_id})-[:BUILT_FROM]-(b:ECRImage {id: $b_id})
        RETURN count(*) as count
        """,
        a_id=child_a_digest,
        b_id=child_b_digest,
    ).single()
    assert sibling_rel["count"] == 0
