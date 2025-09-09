"""
Unit tests for registry-based layer extraction.
"""

import json
import subprocess
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.trivy.layers import check_docker_buildx_available
from cartography.intel.trivy.layers import compute_image_lineage
from cartography.intel.trivy.layers import extract_ecr_info
from cartography.intel.trivy.layers import get_image_layers_from_registry
from cartography.intel.trivy.layers import get_image_platforms


def test_extract_ecr_info():
    # Test valid ECR URL
    registry, region = extract_ecr_info(
        "123456789.dkr.ecr.us-east-1.amazonaws.com/my-repo:tag"
    )
    assert registry == "123456789.dkr.ecr.us-east-1.amazonaws.com"
    assert region == "us-east-1"

    # Test another region
    registry, region = extract_ecr_info(
        "987654321.dkr.ecr.eu-west-2.amazonaws.com/repo:latest"
    )
    assert registry == "987654321.dkr.ecr.eu-west-2.amazonaws.com"
    assert region == "eu-west-2"

    # Test non-ECR URL
    registry, region = extract_ecr_info("docker.io/library/nginx:latest")
    assert registry is None
    assert region is None

    # Test GCR URL
    registry, region = extract_ecr_info("gcr.io/project/image:tag")
    assert registry is None
    assert region is None


def test_compute_image_lineage():
    # Test valid lineage (parent is prefix)
    parent = ["layer1", "layer2", "layer3"]
    child = ["layer1", "layer2", "layer3", "layer4"]
    assert compute_image_lineage(parent, child) is True

    # Test invalid lineage (different prefix)
    parent = ["layer1", "layer2", "layer3"]
    child = ["layer1", "layerX", "layer3", "layer4"]
    assert compute_image_lineage(parent, child) is False

    # Test invalid lineage (parent longer than child)
    parent = ["layer1", "layer2", "layer3", "layer4"]
    child = ["layer1", "layer2"]
    assert compute_image_lineage(parent, child) is False

    # Test empty lists
    assert compute_image_lineage([], ["layer1"]) is False
    assert compute_image_lineage(["layer1"], []) is False
    assert compute_image_lineage([], []) is False

    # Test identical images
    layers = ["layer1", "layer2", "layer3"]
    assert compute_image_lineage(layers, layers) is True


@patch("subprocess.run")
def test_check_docker_buildx_available(mock_run):
    # Test when docker buildx is available
    mock_run.return_value = MagicMock(returncode=0)
    assert check_docker_buildx_available() is True
    mock_run.assert_called_once_with(
        ["docker", "buildx", "imagetools", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    # Test when docker buildx is not available
    mock_run.reset_mock()
    mock_run.return_value = MagicMock(returncode=1)
    assert check_docker_buildx_available() is False

    # Test when docker is not installed
    mock_run.reset_mock()
    mock_run.side_effect = FileNotFoundError()
    assert check_docker_buildx_available() is False


@patch("subprocess.run")
@patch("cartography.intel.trivy.layers.check_docker_buildx_available")
def test_get_image_platforms(mock_check_docker, mock_run):
    mock_check_docker.return_value = True

    # Test multi-arch image (manifest is the index for multi-platform)
    manifest_data = {
        "manifests": [
            {"platform": {"os": "linux", "architecture": "amd64"}},
            {"platform": {"os": "linux", "architecture": "arm64"}},
            {"platform": {"os": "linux", "architecture": "arm", "variant": "v7"}},
        ]
    }
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(manifest_data),
    )

    platforms = get_image_platforms("registry.example.com/image:tag")
    assert platforms == ["linux/amd64", "linux/arm64", "linux/arm/v7"]

    # Test with attestation manifests (should be filtered out)
    manifest_with_attestations = {
        "manifests": [
            {"platform": {"os": "linux", "architecture": "amd64"}},
            {"platform": {"os": "linux", "architecture": "arm64"}},
            {
                "platform": {"os": "unknown", "architecture": "unknown"},
                "annotations": {"vnd.docker.reference.type": "attestation-manifest"},
            },
        ]
    }
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(manifest_with_attestations),
    )
    platforms = get_image_platforms("registry.example.com/image:tag")
    assert platforms == ["linux/amd64", "linux/arm64"]  # attestation filtered out

    # Test single-arch image (no index)
    mock_run.return_value = MagicMock(returncode=0, stdout="")
    platforms = get_image_platforms("registry.example.com/image:tag")
    assert platforms == ["linux/amd64"]  # Default fallback

    # Test error case
    mock_run.side_effect = subprocess.SubprocessError("Error")
    platforms = get_image_platforms("registry.example.com/image:tag")
    assert platforms == ["linux/amd64"]  # Default fallback


@patch("subprocess.run")
@patch("cartography.intel.trivy.layers.check_docker_buildx_available")
@patch("cartography.intel.trivy.layers.get_registry_auth_for_ecr")
def test_get_image_layers_from_registry(mock_auth, mock_check_docker, mock_run):
    mock_check_docker.return_value = True
    mock_auth.return_value = True

    # Test successful layer extraction
    imagetools_output = {
        "Image": {
            "RootFS": {
                "DiffIDs": [
                    "sha256:abc123",
                    "sha256:def456",
                    "sha256:ghi789",
                ]
            },
            "RepoDigests": ["registry.example.com/image@sha256:digest123"],
        },
        "Manifest": {"config": {"digest": "sha256:digest123"}},
    }

    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(imagetools_output),
    )

    diff_ids, digest = get_image_layers_from_registry(
        "123456789.dkr.ecr.us-east-1.amazonaws.com/repo:tag",
        platform="linux/amd64",
    )

    assert diff_ids == ["sha256:abc123", "sha256:def456", "sha256:ghi789"]
    assert digest == "sha256:digest123"

    # Verify auth was called for ECR
    mock_auth.assert_called_once_with(
        "123456789.dkr.ecr.us-east-1.amazonaws.com",
        "us-east-1",
    )

    # Test docker buildx not available
    mock_check_docker.return_value = False
    diff_ids, digest = get_image_layers_from_registry("image:tag")
    assert diff_ids is None
    assert digest is None

    # Test failed inspection
    mock_check_docker.return_value = True
    mock_run.return_value = MagicMock(returncode=1, stderr="Error")
    diff_ids, digest = get_image_layers_from_registry("image:tag")
    assert diff_ids is None
    assert digest is None

    # Test invalid JSON
    mock_run.return_value = MagicMock(returncode=0, stdout="invalid json")
    diff_ids, digest = get_image_layers_from_registry("image:tag")
    assert diff_ids is None
    assert digest is None
