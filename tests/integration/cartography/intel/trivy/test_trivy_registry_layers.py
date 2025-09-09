"""
Integration tests for registry-based layer extraction with docker buildx.
"""

import json
from typing import Any
from typing import Dict
from unittest.mock import MagicMock
from unittest.mock import patch

from neo4j import Session

from cartography.intel.trivy.image_lineage import build_image_layers
from cartography.intel.trivy.image_lineage import compute_ecr_image_lineage
from cartography.intel.trivy.layers import get_image_layers_from_registry
from cartography.intel.trivy.scanner import sync_single_image

# Test constants
TEST_UPDATE_TAG = 123456789

# Mock docker buildx imagetools output based on real ECR image
MOCK_IMAGETOOLS_OUTPUT: Dict[str, Any] = {
    "Image": {
        "created": "2025-09-08T16:17:01.101557715Z",
        "architecture": "amd64",
        "os": "linux",
        "config": {
            "User": "appuser",
            "ExposedPorts": {"8080/tcp": {}},
            "Env": [
                "PATH=/app/.venv/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                "PYTHON_VERSION=3.13.7",
                "APP_USER=appuser",
                "PYTHONUNBUFFERED=1",
                "PYTHONPATH=/app",
            ],
            "Entrypoint": ["dumb-init", "--"],
            "Cmd": ["python", "app.py"],
            "WorkingDir": "/app",
        },
        "RootFS": {
            "Type": "layers",
            "DiffIDs": [
                "sha256:aaa1111111111111111111111111111111111111111111111111111111111111",
                "sha256:bbb2222222222222222222222222222222222222222222222222222222222222",
                "sha256:ccc3333333333333333333333333333333333333333333333333333333333333",
                "sha256:ddd4444444444444444444444444444444444444444444444444444444444444",
                "sha256:eee5555555555555555555555555555555555555555555555555555555555555",
                "sha256:fff6666666666666666666666666666666666666666666666666666666666666",
                "sha256:7777777777777777777777777777777777777777777777777777777777777777",
                "sha256:8888888888888888888888888888888888888888888888888888888888888888",
                "sha256:9999999999999999999999999999999999999999999999999999999999999999",
                "sha256:aaa0000000000000000000000000000000000000000000000000000000000000",
                "sha256:bbb0000000000000000000000000000000000000000000000000000000000000",
                "sha256:ccc0000000000000000000000000000000000000000000000000000000000000",
                "sha256:ddd0000000000000000000000000000000000000000000000000000000000000",
                "sha256:eee0000000000000000000000000000000000000000000000000000000000000",
                "sha256:fff0000000000000000000000000000000000000000000000000000000000000",
            ],
        },
    },
    "Manifest": {
        "config": {
            "digest": "sha256:config11111111111111111111111111111111111111111111111111111111"
        }
    },
}

# Mock Trivy scan output without layer data
MOCK_TRIVY_SCAN_NO_LAYERS: Dict[str, Any] = {
    "ArtifactName": "123456789012.dkr.ecr.us-east-1.amazonaws.com/test-app:v1.0.0",
    "ArtifactType": "container_image",
    "Metadata": {
        "RepoTags": ["123456789012.dkr.ecr.us-east-1.amazonaws.com/test-app:v1.0.0"],
        "RepoDigests": [
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/test-app@sha256:digest111111111111111111111111111111111111111111111111111111"
        ],
        "ImageConfig": {"architecture": "amd64", "os": "linux"},
        # Note: No rootfs.diff_ids field
    },
    "Results": [
        {
            "Target": "test-app:v1.0.0 (debian 12.0)",
            "Class": "os-pkgs",
            "Type": "debian",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2024-0001",
                    "PkgID": "libtest@1.0.0",
                    "PkgName": "libtest",
                    "InstalledVersion": "1.0.0",
                    "FixedVersion": "1.0.1",
                    "Severity": "HIGH",
                    "Description": "Test vulnerability",
                }
            ],
        }
    ],
}

# Mock for child image with extended layers
MOCK_CHILD_IMAGETOOLS_OUTPUT: Dict[str, Any] = {
    "Image": {
        "RootFS": {
            "Type": "layers",
            "DiffIDs": MOCK_IMAGETOOLS_OUTPUT["Image"]["RootFS"]["DiffIDs"]
            + [
                "sha256:child1111111111111111111111111111111111111111111111111111111111",
                "sha256:child2222222222222222222222222222222222222222222222222222222222",
            ],
        }
    },
    "Manifest": {
        "config": {
            "digest": "sha256:childconfig111111111111111111111111111111111111111111111111"
        }
    },
}


@patch("cartography.intel.trivy.layers.subprocess.run")
@patch("cartography.intel.trivy.layers.check_docker_buildx_available")
@patch("cartography.intel.trivy.layers.get_registry_auth_for_ecr")
def test_build_image_layers_from_registry(
    mock_auth, mock_check_docker, mock_run, neo4j_session: Session
):
    """Test building image layers from registry separately from vulnerability scanning."""

    # Clean up any existing layers from previous tests
    neo4j_session.run("MATCH (l:ImageLayer) DETACH DELETE l")

    # Setup mocks
    mock_check_docker.return_value = True
    mock_auth.return_value = True
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(MOCK_IMAGETOOLS_OUTPUT),
    )

    # Seed ECRImage node
    image_digest = "sha256:digest111111111111111111111111111111111111111111111111111111"
    neo4j_session.run("MERGE (:ECRImage {id: $id})", id=image_digest)

    # First build layers using the registry (mocked)
    layers = build_image_layers(
        neo4j_session,
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/test-app:v1.0.0",
        image_digest,
        "linux/amd64",
        TEST_UPDATE_TAG,
    )

    # Then sync Trivy scan results (vulnerabilities only, no layers)
    sync_single_image(
        neo4j_session,
        MOCK_TRIVY_SCAN_NO_LAYERS,
        "test-source",
        TEST_UPDATE_TAG,
    )

    # Verify layers were created from registry
    layer_count = neo4j_session.run(
        "MATCH (l:ImageLayer) RETURN count(l) AS count"
    ).single()["count"]
    assert layers is not None
    assert len(layers) == 15  # All unique layers from mock data

    # Verify layers were created in the graph
    layer_count = neo4j_session.run(
        "MATCH (l:ImageLayer) RETURN count(l) AS count"
    ).single()["count"]
    assert layer_count == 15

    # Verify HEAD and TAIL relationships
    head_tail = neo4j_session.run(
        """
        MATCH (i:ECRImage {id: $id})-[:HEAD]->(h:ImageLayer)
        MATCH (i)-[:TAIL]->(t:ImageLayer)
        RETURN h.diff_id AS head, t.diff_id AS tail, i.length AS length
        """,
        id=image_digest,
    ).single()

    assert head_tail["head"] == MOCK_IMAGETOOLS_OUTPUT["Image"]["RootFS"]["DiffIDs"][0]
    assert head_tail["tail"] == MOCK_IMAGETOOLS_OUTPUT["Image"]["RootFS"]["DiffIDs"][-1]
    assert head_tail["length"] == 15

    # Verify the NEXT relationships form a proper chain
    chain_check = neo4j_session.run(
        """
        MATCH (h:ImageLayer)<-[:HEAD]-(i:ECRImage)-[:TAIL]->(t:ImageLayer)
        MATCH path = (h)-[:NEXT*]->(t)
        WHERE i.id = $id
        RETURN length(path) as path_length
        """,
        id=image_digest,
    ).single()
    assert chain_check["path_length"] == 14  # 15 nodes = 14 edges


@patch("cartography.intel.trivy.layers.subprocess.run")
@patch("cartography.intel.trivy.layers.check_docker_buildx_available")
@patch("cartography.intel.trivy.layers.get_registry_auth_for_ecr")
def test_image_lineage_with_registry_layers(
    mock_auth, mock_check_docker, mock_run, neo4j_session: Session
):
    """Test image lineage detection using registry-extracted layers."""

    # Clean up any existing layers from previous tests
    neo4j_session.run("MATCH (l:ImageLayer) DETACH DELETE l")

    # Setup mocks
    mock_check_docker.return_value = True
    mock_auth.return_value = True

    # Base image
    base_digest = "sha256:basedigest11111111111111111111111111111111111111111111111111"
    base_scan = {
        "ArtifactName": "123456789012.dkr.ecr.us-east-1.amazonaws.com/base-app:v1.0.0",
        "Metadata": {
            "RepoDigests": [
                f"123456789012.dkr.ecr.us-east-1.amazonaws.com/base-app@{base_digest}"
            ]
        },
        "Results": [],
    }

    # Child image (extends base)
    child_digest = "sha256:childdigest1111111111111111111111111111111111111111111111111"
    child_scan = {
        "ArtifactName": "123456789012.dkr.ecr.us-east-1.amazonaws.com/child-app:v2.0.0",
        "Metadata": {
            "RepoDigests": [
                f"123456789012.dkr.ecr.us-east-1.amazonaws.com/child-app@{child_digest}"
            ]
        },
        "Results": [],
    }

    # Seed ECRImage nodes
    neo4j_session.run(
        "UNWIND $ids AS id MERGE (:ECRImage {id: id})", ids=[base_digest, child_digest]
    )

    # Mock base image layers
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(MOCK_IMAGETOOLS_OUTPUT),
    )

    # Build layers for base image
    build_image_layers(
        neo4j_session,
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/base-app:v1.0.0",
        base_digest,
        None,
        TEST_UPDATE_TAG,
    )

    # Sync base scan results
    sync_single_image(
        neo4j_session,
        base_scan,
        "base-source",
        TEST_UPDATE_TAG,
    )

    # Mock child image layers (extends base)
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(MOCK_CHILD_IMAGETOOLS_OUTPUT),
    )

    # Build layers for child image
    build_image_layers(
        neo4j_session,
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/child-app:v2.0.0",
        child_digest,
        None,
        TEST_UPDATE_TAG,
    )

    # Sync child scan results
    sync_single_image(
        neo4j_session,
        child_scan,
        "child-source",
        TEST_UPDATE_TAG,
    )

    # Compute lineage relationships
    compute_ecr_image_lineage(neo4j_session, TEST_UPDATE_TAG)

    # Verify lineage relationship was created
    lineage = neo4j_session.run(
        """
        MATCH (child:ECRImage {id: $child_id})-[:BUILT_FROM]->(base:ECRImage {id: $base_id})
        RETURN count(*) AS count
        """,
        child_id=child_digest,
        base_id=base_digest,
    ).single()

    assert lineage["count"] == 1

    # Verify layer sharing
    total_layers = neo4j_session.run(
        "MATCH (l:ImageLayer) RETURN count(l) AS count"
    ).single()["count"]

    # Should be 17 total unique layers (15 from base + 2 additional from child)
    assert total_layers == 17


@patch("cartography.intel.trivy.layers.subprocess.run")
@patch("cartography.intel.trivy.layers.check_docker_buildx_available")
def test_registry_layers_unavailable_fallback(
    mock_check_docker, mock_run, neo4j_session: Session
):
    """Test graceful fallback when docker buildx is not available."""

    # Clean up any existing layers from previous tests
    neo4j_session.run("MATCH (l:ImageLayer) DETACH DELETE l")

    # Docker buildx not available
    mock_check_docker.return_value = False

    # Seed ECRImage node
    image_digest = "sha256:noregistrydigest111111111111111111111111111111111111111111"
    neo4j_session.run("MERGE (:ECRImage {id: $id})", id=image_digest)

    scan_data = {
        "ArtifactName": "123456789012.dkr.ecr.us-east-1.amazonaws.com/app:v1.0.0",
        "Metadata": {
            "RepoDigests": [
                f"123456789012.dkr.ecr.us-east-1.amazonaws.com/app@{image_digest}"
            ]
        },
        "Results": [],
    }

    # When docker buildx is not available, build_image_layers returns None
    # This should not crash
    layers = build_image_layers(
        neo4j_session,
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/app:v1.0.0",
        image_digest,
        None,
        TEST_UPDATE_TAG,
    )

    assert layers is None  # No layers since docker buildx not available

    # Vulnerability scanning should still work
    sync_single_image(
        neo4j_session,
        scan_data,
        "test-source",
        TEST_UPDATE_TAG,
    )

    # Verify no layers were created
    layer_count = neo4j_session.run(
        "MATCH (l:ImageLayer) RETURN count(l) AS count"
    ).single()["count"]
    assert layer_count == 0

    # Docker buildx should not have been called
    mock_run.assert_not_called()


@patch("cartography.intel.trivy.layers.subprocess.run")
@patch("cartography.intel.trivy.layers.check_docker_buildx_available")
def test_multi_platform_image_handling(
    mock_check_docker, mock_run, neo4j_session: Session
):
    """Test handling of multi-platform images."""

    mock_check_docker.return_value = True

    # Mock single return (get_image_layers_from_registry calls once with platform specified)
    mock_run.return_value = MagicMock(
        returncode=0, stdout=json.dumps(MOCK_IMAGETOOLS_OUTPUT)
    )

    # Get layers for specific platform
    diff_ids, digest = get_image_layers_from_registry(
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/multi-arch:latest",
        platform="linux/amd64",
    )

    assert diff_ids == MOCK_IMAGETOOLS_OUTPUT["Image"]["RootFS"]["DiffIDs"]
    assert digest == MOCK_IMAGETOOLS_OUTPUT["Manifest"]["config"]["digest"]

    # Verify we extracted the expected layers from the mocked output
    assert len(diff_ids) == 15
    assert diff_ids[0].startswith("sha256:")
    assert digest.startswith("sha256:")
