import asyncio
import logging
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import httpx
import pytest
from botocore.exceptions import ClientError

import tests.data.aws.ecr as test_data
from cartography.intel.aws.ecr_image_layers import batch_get_manifest
from cartography.intel.aws.ecr_image_layers import ECRLayerFetchTransientError
from cartography.intel.aws.ecr_image_layers import extract_repo_uri_from_image_uri
from cartography.intel.aws.ecr_image_layers import fetch_image_layers_async
from cartography.intel.aws.ecr_image_layers import get_blob_json_via_presigned
from cartography.intel.aws.ecr_image_layers import transform_ecr_image_layers
from cartography.intel.supply_chain import extract_workflow_path_from_ref


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


@pytest.mark.parametrize("error_code", ["AccessDenied", "AccessDeniedException"])
def test_batch_get_manifest_access_denied_returns_empty_result(error_code):
    """Test that access-denied errors are non-fatal when fetching manifests."""
    mock_ecr_client = AsyncMock()
    mock_ecr_client.batch_get_image.side_effect = ClientError(
        {
            "Error": {
                "Code": error_code,
                "Message": "Not authorized to perform ecr:BatchGetImage",
            }
        },
        "BatchGetImage",
    )

    manifest, media_type = asyncio.run(
        batch_get_manifest(
            mock_ecr_client,
            "example/repository",
            "sha256:12345",
            ["application/vnd.oci.image.manifest.v1+json"],
        )
    )

    assert manifest == {}
    assert media_type == ""


def test_batch_get_manifest_transient_aws_error_raises_skip_signal():
    mock_ecr_client = AsyncMock()
    mock_ecr_client.batch_get_image.side_effect = ClientError(
        {
            "Error": {
                "Code": "ServiceUnavailableException",
                "Message": "Try again later",
            },
            "ResponseMetadata": {"HTTPStatusCode": 503},
        },
        "BatchGetImage",
    )

    with pytest.raises(ECRLayerFetchTransientError):
        asyncio.run(
            batch_get_manifest(
                mock_ecr_client,
                "example/repository",
                "sha256:12345",
                ["application/vnd.oci.image.manifest.v1+json"],
            )
        )


def test_get_blob_json_via_presigned_retries_remote_protocol_error(mocker):
    mock_ecr_client = AsyncMock()
    mock_ecr_client.get_download_url_for_layer.return_value = {
        "downloadUrl": "https://example.com/blob"
    }

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"value": "ok"}

    http_client = AsyncMock()
    http_client.get.side_effect = [
        httpx.RemoteProtocolError("Server disconnected without sending a response."),
        response,
    ]

    sleep = mocker.patch(
        "cartography.intel.aws.ecr_image_layers.asyncio.sleep",
        new=AsyncMock(),
    )

    result = asyncio.run(
        get_blob_json_via_presigned(
            mock_ecr_client,
            "example/repository",
            "sha256:12345",
            http_client,
        )
    )

    assert result == {"value": "ok"}
    assert http_client.get.await_count == 2
    sleep.assert_awaited_once()


def test_get_blob_json_via_presigned_raises_skip_signal_after_retry_exhaustion(mocker):
    mock_ecr_client = AsyncMock()
    mock_ecr_client.get_download_url_for_layer.return_value = {
        "downloadUrl": "https://example.com/blob"
    }

    http_client = AsyncMock()
    http_client.get.side_effect = [
        httpx.ReadError("boom"),
        httpx.ReadError("boom"),
        httpx.ReadError("boom"),
    ]

    mocker.patch(
        "cartography.intel.aws.ecr_image_layers.asyncio.sleep",
        new=AsyncMock(),
    )

    with pytest.raises(ECRLayerFetchTransientError):
        asyncio.run(
            get_blob_json_via_presigned(
                mock_ecr_client,
                "example/repository",
                "sha256:12345",
                http_client,
            )
        )


def test_get_blob_json_via_presigned_redacts_presigned_url_in_http_status_logs(
    mocker, caplog
):
    mock_ecr_client = AsyncMock()
    signed_url = "https://example.com/blob?X-Amz-Signature=SECRET&X-Amz-Credential=ABC"
    mock_ecr_client.get_download_url_for_layer.return_value = {
        "downloadUrl": signed_url
    }

    request = httpx.Request("GET", signed_url)
    response = httpx.Response(503, request=request)
    status_error = httpx.HTTPStatusError(
        "boom",
        request=request,
        response=response,
    )

    http_client = AsyncMock()
    http_client.get.side_effect = [status_error, status_error, status_error]

    mocker.patch(
        "cartography.intel.aws.ecr_image_layers.asyncio.sleep",
        new=AsyncMock(),
    )

    with caplog.at_level(logging.WARNING):
        with pytest.raises(ECRLayerFetchTransientError):
            asyncio.run(
                get_blob_json_via_presigned(
                    mock_ecr_client,
                    "example/repository",
                    "sha256:12345",
                    http_client,
                )
            )

    assert "X-Amz-Signature" not in caplog.text
    assert "HTTPStatusError(status_code=503)" in caplog.text


def test_fetch_image_layers_async_skips_only_transient_image_failure(mocker):
    repo_uri = "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository"
    repo_images_list = [
        {
            "uri": f"{repo_uri}:bad",
            "imageDigest": "sha256:bad",
            "repo_uri": repo_uri,
        },
        {
            "uri": f"{repo_uri}:good",
            "imageDigest": "sha256:good",
            "repo_uri": repo_uri,
        },
    ]

    async def mock_batch_get_manifest(_client, _repo, image_ref, _accepted):
        if image_ref == "sha256:bad":
            raise ECRLayerFetchTransientError("temporary failure")
        return (
            test_data.SAMPLE_MANIFEST,
            "application/vnd.docker.distribution.manifest.v2+json",
        )

    mocker.patch(
        "cartography.intel.aws.ecr_image_layers.batch_get_manifest",
        side_effect=mock_batch_get_manifest,
    )
    mocker.patch(
        "cartography.intel.aws.ecr_image_layers.get_blob_json_via_presigned",
        new=AsyncMock(return_value=test_data.SAMPLE_CONFIG_BLOB),
    )

    image_layers_data, image_digest_map, history_by_diff_id, image_attestation_map = (
        asyncio.run(
            fetch_image_layers_async(
                AsyncMock(),
                repo_images_list,
                max_concurrent=2,
            )
        )
    )

    assert f"{repo_uri}:bad" not in image_layers_data
    assert f"{repo_uri}:good" in image_layers_data
    assert image_digest_map == {f"{repo_uri}:good": "sha256:good"}
    assert isinstance(history_by_diff_id, dict)
    assert image_attestation_map == {}


def test_fetch_image_layers_async_skips_manifest_list_image_when_child_fetch_fails(
    mocker,
):
    repo_uri = "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository"
    repo_images_list = [
        {
            "uri": f"{repo_uri}:manifest-list",
            "imageDigest": "sha256:manifest-list",
            "repo_uri": repo_uri,
        },
    ]

    async def mock_batch_get_manifest(_client, _repo, image_ref, _accepted):
        if image_ref == "sha256:manifest-list":
            return (
                test_data.SAMPLE_MANIFEST_LIST,
                "application/vnd.docker.distribution.manifest.list.v2+json",
            )
        if (
            image_ref
            == "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1"
        ):
            return (
                test_data.SAMPLE_MANIFEST,
                "application/vnd.docker.distribution.manifest.v2+json",
            )
        raise ECRLayerFetchTransientError("temporary child failure")

    mocker.patch(
        "cartography.intel.aws.ecr_image_layers.batch_get_manifest",
        side_effect=mock_batch_get_manifest,
    )
    mocker.patch(
        "cartography.intel.aws.ecr_image_layers.get_blob_json_via_presigned",
        new=AsyncMock(return_value=test_data.SAMPLE_CONFIG_BLOB),
    )

    image_layers_data, image_digest_map, history_by_diff_id, image_attestation_map = (
        asyncio.run(
            fetch_image_layers_async(
                AsyncMock(),
                repo_images_list,
                max_concurrent=4,
            )
        )
    )

    assert image_layers_data == {}
    assert image_digest_map == {}
    assert history_by_diff_id == {}
    assert image_attestation_map == {}


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


def test_transform_ecr_image_layers_with_attestation_data():
    """Test that attestation data is correctly added to memberships."""
    image_layers_data = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/backend:latest": {
            "linux/amd64": [
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                "sha256:2222222222222222222222222222222222222222222222222222222222222222",
            ]
        }
    }

    image_digest_map = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/backend:latest": "sha256:aaaa000000000000000000000000000000000000000000000000000000000001"
    }

    image_attestation_map = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/backend:latest": {
            "parent_image_uri": "pkg:docker/123456789012.dkr.ecr.us-east-1.amazonaws.com/base-images@abc123",
            "parent_image_digest": "sha256:bbbb000000000000000000000000000000000000000000000000000000000001",
        }
    }

    layers, memberships = transform_ecr_image_layers(
        image_layers_data,
        image_digest_map,
        None,  # history_by_diff_id
        image_attestation_map,
    )

    # Should have 2 layers
    assert len(layers) == 2

    # Should have 1 membership with attestation data
    assert len(memberships) == 1
    membership = memberships[0]

    assert (
        membership["imageDigest"]
        == "sha256:aaaa000000000000000000000000000000000000000000000000000000000001"
    )
    assert len(membership["layer_diff_ids"]) == 2
    assert (
        membership["parent_image_uri"]
        == "pkg:docker/123456789012.dkr.ecr.us-east-1.amazonaws.com/base-images@abc123"
    )
    assert (
        membership["parent_image_digest"]
        == "sha256:bbbb000000000000000000000000000000000000000000000000000000000001"
    )


def test_transform_ecr_image_layers_without_attestation_data():
    """Test that transform works without attestation data (backward compatibility)."""
    image_layers_data = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/backend:latest": {
            "linux/amd64": [
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            ]
        }
    }

    image_digest_map = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/backend:latest": "sha256:aaaa000000000000000000000000000000000000000000000000000000000001"
    }

    # No attestation map provided
    layers, memberships = transform_ecr_image_layers(
        image_layers_data,
        image_digest_map,
    )

    # Should work without errors
    assert len(layers) == 1
    assert len(memberships) == 1

    membership = memberships[0]
    # Should NOT have parent_image_uri or parent_image_digest
    assert "parent_image_uri" not in membership
    assert "parent_image_digest" not in membership


def test_transform_ecr_image_layers_with_history():
    """Test that history commands are correctly added to layers."""
    image_layers_data = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/app:latest": {
            "linux/amd64": [
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                "sha256:2222222222222222222222222222222222222222222222222222222222222222",
                "sha256:3333333333333333333333333333333333333333333333333333333333333333",
            ]
        }
    }

    image_digest_map = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/app:latest": "sha256:aaaa000000000000000000000000000000000000000000000000000000000001"
    }

    history_by_diff_id = {
        "sha256:1111111111111111111111111111111111111111111111111111111111111111": "/bin/sh -c #(nop) ADD file:abc123 in /",
        "sha256:2222222222222222222222222222222222222222222222222222222222222222": "/bin/sh -c apt-get update && apt-get install -y python3",
        "sha256:3333333333333333333333333333333333333333333333333333333333333333": "/bin/sh -c #(nop) COPY dir:xyz789 in /app",
    }

    layers, memberships = transform_ecr_image_layers(
        image_layers_data,
        image_digest_map,
        history_by_diff_id,
    )

    # Should have 3 layers
    assert len(layers) == 3

    # Each layer should have its history command
    for layer in layers:
        diff_id = layer["diff_id"]
        assert "history" in layer, f"Layer {diff_id} should have history"
        assert layer["history"] == history_by_diff_id[diff_id]


def test_transform_ecr_image_layers_with_partial_history():
    """Test that layers without history in the map don't get a history field."""
    image_layers_data = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/app:latest": {
            "linux/amd64": [
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",
                "sha256:2222222222222222222222222222222222222222222222222222222222222222",
            ]
        }
    }

    image_digest_map = {
        "123456789012.dkr.ecr.us-east-1.amazonaws.com/app:latest": "sha256:aaaa000000000000000000000000000000000000000000000000000000000001"
    }

    # Only first layer has history
    history_by_diff_id = {
        "sha256:1111111111111111111111111111111111111111111111111111111111111111": "/bin/sh -c #(nop) ADD file:abc123 in /",
    }

    layers, memberships = transform_ecr_image_layers(
        image_layers_data,
        image_digest_map,
        history_by_diff_id,
    )

    # Should have 2 layers
    assert len(layers) == 2

    # Find each layer
    layer1 = next(
        layer
        for layer in layers
        if layer["diff_id"]
        == "sha256:1111111111111111111111111111111111111111111111111111111111111111"
    )
    layer2 = next(
        layer
        for layer in layers
        if layer["diff_id"]
        == "sha256:2222222222222222222222222222222222222222222222222222222222222222"
    )

    # First layer should have history
    assert "history" in layer1
    assert layer1["history"] == "/bin/sh -c #(nop) ADD file:abc123 in /"

    # Second layer should NOT have history field (not in map)
    assert "history" not in layer2


@pytest.mark.parametrize(
    "workflow_ref,expected_path",
    [
        # Standard GitHub workflow ref
        (
            "subimagesec/subimage/.github/workflows/docker-push-subimage.yaml@refs/pull/1042/merge",
            ".github/workflows/docker-push-subimage.yaml",
        ),
        # Workflow ref with refs/heads/main
        (
            "owner/repo/.github/workflows/build.yaml@refs/heads/main",
            ".github/workflows/build.yaml",
        ),
        # Workflow ref with tag
        (
            "myorg/myrepo/.github/workflows/release.yml@refs/tags/v1.0.0",
            ".github/workflows/release.yml",
        ),
        # Nested workflow path
        (
            "org/repo/ci/workflows/test.yaml@refs/heads/develop",
            "ci/workflows/test.yaml",
        ),
        # Empty string
        ("", None),
        # None value
        (None, None),
        # No @ suffix (edge case)
        (
            "owner/repo/.github/workflows/build.yaml",
            ".github/workflows/build.yaml",
        ),
    ],
)
def testextract_workflow_path_from_ref(workflow_ref, expected_path):
    """Test extracting workflow path from GitHub workflow ref."""
    assert extract_workflow_path_from_ref(workflow_ref) == expected_path
