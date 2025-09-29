import pytest

from cartography.intel.aws.ecr_image_layers import extract_repo_uri_from_image_uri
from cartography.intel.aws.ecr_image_layers import transform_ecr_image_layers


def test_extract_repo_uri_from_image_uri():
    """Test the extract_repo_uri_from_image_uri helper function."""

    test_cases = [
        # Format: (input_uri, expected_repo_uri)
        # Digest-based URI
        (
            "123456789.dkr.ecr.us-east-1.amazonaws.com/my-repo@sha256:abcdef123456789",
            "123456789.dkr.ecr.us-east-1.amazonaws.com/my-repo",
        ),
        # Tag-based URI
        (
            "123456789.dkr.ecr.us-east-1.amazonaws.com/my-repo:v1.0.0",
            "123456789.dkr.ecr.us-east-1.amazonaws.com/my-repo",
        ),
        # No tag or digest
        (
            "123456789.dkr.ecr.us-east-1.amazonaws.com/my-repo",
            "123456789.dkr.ecr.us-east-1.amazonaws.com/my-repo",
        ),
        # Complex repository name with slashes
        (
            "123456789.dkr.ecr.us-west-2.amazonaws.com/team/service/component:latest",
            "123456789.dkr.ecr.us-west-2.amazonaws.com/team/service/component",
        ),
        # Tag with multiple colons in name
        (
            "123456789.dkr.ecr.us-east-1.amazonaws.com/namespace/my-repo:v1.0.0",
            "123456789.dkr.ecr.us-east-1.amazonaws.com/namespace/my-repo",
        ),
        # Port in tag (edge case)
        (
            "123456789.dkr.ecr.eu-west-1.amazonaws.com/app:build-123",
            "123456789.dkr.ecr.eu-west-1.amazonaws.com/app",
        ),
    ]

    for input_uri, expected_repo_uri in test_cases:
        actual_repo_uri = extract_repo_uri_from_image_uri(input_uri)
        assert actual_repo_uri == expected_repo_uri, (
            f"URI extraction failed for {input_uri}. "
            f"Expected: {expected_repo_uri}, Got: {actual_repo_uri}"
        )


def test_extract_repo_uri_edge_cases():
    """Test edge cases for the extract_repo_uri_from_image_uri function."""

    edge_cases = [
        # Empty string
        ("", ""),
        # Only digest marker (malformed)
        ("@sha256:", ""),
        # Only colon (malformed)
        (":", ""),
        # Multiple @ symbols (should split on first)
        ("repo@sha256:abc@def", "repo"),
        # Mixed digest and tag markers (digest takes precedence)
        ("repo@sha256:abc:tag", "repo"),
    ]

    for input_uri, expected_repo_uri in edge_cases:
        actual_repo_uri = extract_repo_uri_from_image_uri(input_uri)
        assert actual_repo_uri == expected_repo_uri, (
            f"Edge case URI extraction failed for {input_uri}. "
            f"Expected: {expected_repo_uri}, Got: {actual_repo_uri}"
        )


def test_transform_ecr_image_layers_basic():
    """Basic test for transform_ecr_image_layers function."""
    image_layers_data = {
        "repo/image:tag": {"linux/amd64": ["sha256:layer1", "sha256:layer2"]}
    }
    image_digest_map = {"repo/image:tag": "sha256:imagedigest"}

    layers, memberships = transform_ecr_image_layers(
        image_layers_data, image_digest_map
    )

    # Should have 2 layers
    assert len(layers) == 2

    # Should have 1 membership
    assert len(memberships) == 1
    assert memberships[0]["imageDigest"] == "sha256:imagedigest"
    assert memberships[0]["layer_diff_ids"] == ["sha256:layer1", "sha256:layer2"]


def test_transform_ecr_image_layers_missing_digest_fails():
    """Test that transform_ecr_image_layers fails when digest is missing from map."""
    image_layers_data = {"repo/image:tag": {"linux/amd64": ["sha256:layer1"]}}
    image_digest_map = {}  # Missing the digest mapping

    # Should raise KeyError since we use direct dictionary access
    with pytest.raises(KeyError):
        transform_ecr_image_layers(image_layers_data, image_digest_map)


def test_transform_ecr_image_layers_empty_input():
    """Test transform_ecr_image_layers with empty input."""
    layers, memberships = transform_ecr_image_layers({}, {})

    assert layers == []
    assert memberships == []
