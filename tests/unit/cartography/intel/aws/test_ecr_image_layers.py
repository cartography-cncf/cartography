import pytest

from cartography.intel.aws.ecr_image_layers import extract_repo_uri_from_image_uri
from cartography.intel.aws.ecr_image_layers import transform_ecr_image_layers


@pytest.mark.parametrize(
    "input_uri,expected_repo_uri",
    [
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
        # Edge cases
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
    ],
)
def test_extract_repo_uri_from_image_uri(input_uri, expected_repo_uri):
    """Test the extract_repo_uri_from_image_uri helper function."""
    actual_repo_uri = extract_repo_uri_from_image_uri(input_uri)
    assert actual_repo_uri == expected_repo_uri


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


def test_transform_layers_creates_graph_structure():
    """Test that transform creates proper graph structure from layer data."""
    # Test images sharing base layers (common in Docker)
    image_layers_data = {
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/web-app:v1": {
            "linux/amd64": [
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",  # base OS layer
                "sha256:2222222222222222222222222222222222222222222222222222222222222222",  # runtime layer
                "sha256:3333333333333333333333333333333333333333333333333333333333333333",  # app-specific
            ]
        },
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/api-service:v1": {
            "linux/amd64": [
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",  # shared base
                "sha256:2222222222222222222222222222222222222222222222222222222222222222",  # shared runtime
                "sha256:4444444444444444444444444444444444444444444444444444444444444444",  # api-specific
            ]
        },
    }

    image_digest_map = {
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/web-app:v1": "sha256:aaaa000000000000000000000000000000000000000000000000000000000001",
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/api-service:v1": "sha256:bbbb000000000000000000000000000000000000000000000000000000000001",
    }

    layers, memberships = transform_ecr_image_layers(
        image_layers_data,
        image_digest_map,
    )

    # Should have 4 unique layers (2 shared, 2 unique)
    assert len(layers) == 4

    # Base layer should be HEAD of both images
    base_layer = next(
        layer
        for layer in layers
        if layer["diff_id"]
        == "sha256:1111111111111111111111111111111111111111111111111111111111111111"
    )
    assert len(base_layer["head_image_ids"]) == 2
    assert (
        "sha256:aaaa000000000000000000000000000000000000000000000000000000000001"
        in base_layer["head_image_ids"]
    )
    assert (
        "sha256:bbbb000000000000000000000000000000000000000000000000000000000001"
        in base_layer["head_image_ids"]
    )
    # Base layer should have NEXT pointing to runtime layer
    assert base_layer["next_diff_ids"] == [
        "sha256:2222222222222222222222222222222222222222222222222222222222222222"
    ]

    # Runtime layer should have NEXT pointing to both app-specific layers (divergence point)
    runtime_layer = next(
        layer
        for layer in layers
        if layer["diff_id"]
        == "sha256:2222222222222222222222222222222222222222222222222222222222222222"
    )
    assert set(runtime_layer["next_diff_ids"]) == {
        "sha256:3333333333333333333333333333333333333333333333333333333333333333",
        "sha256:4444444444444444444444444444444444444444444444444444444444444444",
    }

    # App-specific layers should be TAIL of their respective images
    web_layer = next(
        layer
        for layer in layers
        if layer["diff_id"]
        == "sha256:3333333333333333333333333333333333333333333333333333333333333333"
    )
    assert web_layer["tail_image_ids"] == [
        "sha256:aaaa000000000000000000000000000000000000000000000000000000000001"
    ]

    api_layer = next(
        layer
        for layer in layers
        if layer["diff_id"]
        == "sha256:4444444444444444444444444444444444444444444444444444444444444444"
    )
    assert api_layer["tail_image_ids"] == [
        "sha256:bbbb000000000000000000000000000000000000000000000000000000000001"
    ]
    # TAIL layers should have no NEXT relationships
    assert "next_diff_ids" not in web_layer
    assert "next_diff_ids" not in api_layer

    # Memberships should correspond to both images' layer sequences
    expected_memberships = {
        (
            "sha256:aaaa000000000000000000000000000000000000000000000000000000000001",
            (
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                "sha256:2222222222222222222222222222222222222222222222222222222222222222",
                "sha256:3333333333333333333333333333333333333333333333333333333333333333",
            ),
        ),
        (
            "sha256:bbbb000000000000000000000000000000000000000000000000000000000001",
            (
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                "sha256:2222222222222222222222222222222222222222222222222222222222222222",
                "sha256:4444444444444444444444444444444444444444444444444444444444444444",
            ),
        ),
    }

    observed_memberships = {
        (m["imageDigest"], tuple(m["layer_diff_ids"])) for m in memberships
    }
    assert observed_memberships == expected_memberships
