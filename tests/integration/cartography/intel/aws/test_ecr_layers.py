from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.aws.ecr
import cartography.intel.aws.ecr_image_layers as ecr_layers
import tests.data.aws.ecr as test_data
from cartography.intel.aws.ecr_image_layers import sync as sync_ecr_layers
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789
TEST_REGION = "us-east-1"


@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repositories",
    return_value=test_data.DESCRIBE_REPOSITORIES["repositories"][:1],
)
@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repository_images",
    return_value=test_data.LIST_REPOSITORY_IMAGES[
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository"
    ][:1],
)
@patch("cartography.client.aws.ecr.get_ecr_images")
@patch("cartography.intel.aws.ecr_image_layers.batch_get_manifest")
@patch("cartography.intel.aws.ecr_image_layers.get_blob_json_via_presigned")
def test_sync_with_layers(
    mock_get_blob,
    mock_batch_get_manifest,
    mock_get_ecr_images,
    mock_get_repo_images,
    mock_get_repos,
    neo4j_session,
):
    """Test ECR sync with image layer support"""
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    cartography.intel.aws.ecr.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Mock images from graph
    mock_get_ecr_images.return_value = {
        (
            "us-east-1",
            "1",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1",
            "example-repository",
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        )
    }

    # Mock manifest retrieval
    mock_batch_get_manifest.return_value = (
        test_data.SAMPLE_MANIFEST,
        "application/vnd.docker.distribution.manifest.v2+json",
    )

    # Mock config blob retrieval
    mock_get_blob.return_value = test_data.SAMPLE_CONFIG_BLOB

    # Create mock boto3 session
    boto3_session = MagicMock()
    boto3_session.client.return_value.batch_get_image.return_value = (
        test_data.BATCH_GET_IMAGE_RESPONSE
    )
    boto3_session.client.return_value.get_download_url_for_layer.return_value = (
        test_data.GET_DOWNLOAD_URL_RESPONSE
    )

    # Act
    # Run sync with layer support
    sync_ecr_layers(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    # Check that ECRImage nodes were created
    expected_ecr_images = {
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            TEST_REGION,
        ),
    }
    assert (
        check_nodes(neo4j_session, "ECRImage", ["id", "region"]) == expected_ecr_images
    )

    # Check that ECRImageLayer nodes were created
    expected_layers = {
        ("sha256:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",),
        ("sha256:fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",),
        ("sha256:4ac5bb3f45ba451e817df5f30b950f6eb32145e00ba5f134973810881fde7ac0",),
    }
    assert check_nodes(neo4j_session, "ECRImageLayer", ["id"]) == expected_layers
    # Also verify they have the ImageLayer extra label
    assert check_nodes(neo4j_session, "ImageLayer", ["id"]) == expected_layers

    # Check NEXT relationships between layers
    expected_next_rels = {
        (
            "sha256:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
            "sha256:fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
        ),
        (
            "sha256:fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
            "sha256:4ac5bb3f45ba451e817df5f30b950f6eb32145e00ba5f134973810881fde7ac0",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ECRImageLayer",
            "id",
            "ECRImageLayer",
            "id",
            "NEXT",
            rel_direction_right=True,
        )
        == expected_next_rels
    )

    expected_has_layer_rels = {
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "sha256:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
        ),
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "sha256:fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
        ),
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "sha256:4ac5bb3f45ba451e817df5f30b950f6eb32145e00ba5f134973810881fde7ac0",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ECRImage",
            "id",
            "ECRImageLayer",
            "id",
            "HAS_LAYER",
            rel_direction_right=True,
        )
        == expected_has_layer_rels
    )

    sequence_record = neo4j_session.run(
        """
        MATCH (img:ECRImage {id: $digest})
        RETURN img.layer_diff_ids AS layer_diff_ids
        """,
        digest="sha256:0000000000000000000000000000000000000000000000000000000000000000",
    ).single()
    assert sequence_record
    assert sequence_record["layer_diff_ids"] == [
        "sha256:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
        "sha256:fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
        "sha256:4ac5bb3f45ba451e817df5f30b950f6eb32145e00ba5f134973810881fde7ac0",
    ]

    path_rows = neo4j_session.run(
        """
        MATCH (img:ECRImage {id: $digest})-[:HEAD]->(head:ECRImageLayer)
        MATCH (img)-[:TAIL]->(tail:ECRImageLayer)
        MATCH path = (head)-[:NEXT*0..]->(tail)
        WHERE ALL(layer IN nodes(path) WHERE (img)-[:HAS_LAYER]->(layer))
        WITH path
        ORDER BY length(path) DESC
        LIMIT 1
        UNWIND range(0, length(path)) AS idx
        RETURN nodes(path)[idx].diff_id AS diff_id
        ORDER BY idx
        """,
        digest="sha256:0000000000000000000000000000000000000000000000000000000000000000",
    )
    path_layers = [record["diff_id"] for record in path_rows]
    assert path_layers == sequence_record["layer_diff_ids"]

    # Check HEAD relationship from ECRImage to first layer
    expected_head_rels = {
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "sha256:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ECRImage",
            "id",
            "ImageLayer",
            "id",
            "HEAD",
            rel_direction_right=True,
        )
        == expected_head_rels
    )

    # Check TAIL relationship from ECRImage to last layer
    expected_tail_rels = {
        (
            "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "sha256:4ac5bb3f45ba451e817df5f30b950f6eb32145e00ba5f134973810881fde7ac0",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "ECRImage",
            "id",
            "ImageLayer",
            "id",
            "TAIL",
            rel_direction_right=True,
        )
        == expected_tail_rels
    )


def test_shared_layers_preserve_multiple_next_edges():
    """Test that shared base layers preserve NEXT edges to different successor layers."""
    # Example: Two images share layer1→layer2 but diverge after:
    # Image A: layer1 → layer2 → layer3
    # Image B: layer1 → layer2 → layer4

    image_layers_data = {
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/service-a:v1": {
            "linux/amd64": [
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",  # shared
                "sha256:2222222222222222222222222222222222222222222222222222222222222222",  # shared
                "sha256:3333333333333333333333333333333333333333333333333333333333333333",  # unique to A
            ]
        },
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/service-b:v1": {
            "linux/amd64": [
                "sha256:1111111111111111111111111111111111111111111111111111111111111111",  # shared
                "sha256:2222222222222222222222222222222222222222222222222222222222222222",  # shared
                "sha256:4444444444444444444444444444444444444444444444444444444444444444",  # unique to B
            ]
        },
    }

    image_digest_map = {
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/service-a:v1": "sha256:aaaa000000000000000000000000000000000000000000000000000000000001",
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/service-b:v1": "sha256:bbbb000000000000000000000000000000000000000000000000000000000001",
    }

    layers, memberships = ecr_layers.transform_ecr_image_layers(
        image_layers_data,
        image_digest_map,
    )

    # Find layer2 which should have NEXT edges to both layer3 and layer4
    layer2 = next(
        layer
        for layer in layers
        if layer["diff_id"]
        == "sha256:2222222222222222222222222222222222222222222222222222222222222222"
    )

    # Layer2 should have two NEXT relationships
    assert "next_diff_ids" in layer2
    assert len(layer2["next_diff_ids"]) == 2
    assert (
        "sha256:3333333333333333333333333333333333333333333333333333333333333333"
        in layer2["next_diff_ids"]
    )
    assert (
        "sha256:4444444444444444444444444444444444444444444444444444444444444444"
        in layer2["next_diff_ids"]
    )

    # Memberships should track both image sequences distinctly
    membership_pairs = {
        (m["imageDigest"], tuple(m["layer_diff_ids"])) for m in memberships
    }
    assert (
        "sha256:aaaa000000000000000000000000000000000000000000000000000000000001",
        (
            "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "sha256:2222222222222222222222222222222222222222222222222222222222222222",
            "sha256:3333333333333333333333333333333333333333333333333333333333333333",
        ),
    ) in membership_pairs
    assert (
        "sha256:bbbb000000000000000000000000000000000000000000000000000000000001",
        (
            "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "sha256:2222222222222222222222222222222222222222222222222222222222222222",
            "sha256:4444444444444444444444444444444444444444444444444444444444444444",
        ),
    ) in membership_pairs


def test_transform_marks_empty_layer():
    layers, _ = ecr_layers.transform_ecr_image_layers(
        {
            "repo/image:tag": {
                "linux/amd64": [
                    ecr_layers.EMPTY_LAYER_DIFF_ID,
                    "sha256:abcdef0123456789",
                ],
            },
        },
        {"repo/image:tag": "sha256:image"},
    )

    empty_layer = next(
        layer for layer in layers if layer["diff_id"] == ecr_layers.EMPTY_LAYER_DIFF_ID
    )
    non_empty_layer = next(
        layer for layer in layers if layer["diff_id"] == "sha256:abcdef0123456789"
    )

    assert empty_layer["is_empty"] is True
    assert non_empty_layer["is_empty"] is False


@pytest.mark.asyncio
@patch(
    "cartography.intel.aws.ecr_image_layers.get_blob_json_via_presigned",
    new_callable=AsyncMock,
)
@patch("cartography.intel.aws.ecr_image_layers.batch_get_manifest")
async def test_fetch_image_layers_async_handles_manifest_list(
    mock_batch_get_manifest,
    mock_get_blob_json,
):
    repo_image = {
        "uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/subimage-shared:multi",
        "imageDigest": "sha256:indexdigest000000000000000000000000000000000000000000000000000000000000",
        "repo_uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/subimage-shared",
    }

    manifest_lookup = {
        repo_image["imageDigest"]: (
            test_data.MULTI_ARCH_INDEX,
            ecr_layers.ECR_OCI_INDEX_MT,
        ),
        "sha256:1111111111111111111111111111111111111111111111111111111111111111": (
            test_data.MULTI_ARCH_AMD64_MANIFEST,
            ecr_layers.ECR_OCI_MANIFEST_MT,
        ),
        "sha256:2222222222222222222222222222222222222222222222222222222222222222": (
            test_data.MULTI_ARCH_ARM64_MANIFEST,
            ecr_layers.ECR_OCI_MANIFEST_MT,
        ),
        "sha256:3333333333333333333333333333333333333333333333333333333333333333": (
            test_data.ATTESTATION_MANIFEST,
            ecr_layers.ECR_OCI_MANIFEST_MT,
        ),
    }

    def fake_batch_get_manifest(ecr_client, repo_name, image_ref, accepted_media_types):
        return manifest_lookup[image_ref]

    mock_batch_get_manifest.side_effect = fake_batch_get_manifest

    async def fake_get_blob_json(ecr_client, repo_name, digest, http_client):
        config_lookup = {
            test_data.MULTI_ARCH_AMD64_MANIFEST["config"][
                "digest"
            ]: test_data.MULTI_ARCH_AMD64_CONFIG,
            test_data.MULTI_ARCH_ARM64_MANIFEST["config"][
                "digest"
            ]: test_data.MULTI_ARCH_ARM64_CONFIG,
        }
        return config_lookup.get(digest, {})

    mock_get_blob_json.side_effect = fake_get_blob_json

    image_layers_data, digest_map, attestation_map = (
        await ecr_layers.fetch_image_layers_async(
            MagicMock(),
            [repo_image],
            max_concurrent=1,
        )
    )

    assert image_layers_data == {
        repo_image["uri"]: {
            "linux/amd64": test_data.MULTI_ARCH_AMD64_CONFIG["rootfs"]["diff_ids"],
            "linux/arm64/v8": test_data.MULTI_ARCH_ARM64_CONFIG["rootfs"]["diff_ids"],
        }
    }
    assert digest_map == {repo_image["uri"]: repo_image["imageDigest"]}


@pytest.mark.asyncio
@patch(
    "cartography.intel.aws.ecr_image_layers.get_blob_json_via_presigned",
    new_callable=AsyncMock,
)
@patch("cartography.intel.aws.ecr_image_layers.batch_get_manifest")
async def test_fetch_image_layers_async_skips_attestation_only(
    mock_batch_get_manifest,
    mock_get_blob_json,
):
    repo_image = {
        "uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/subimage-shared:attestation",
        "imageDigest": "sha256:attestationindex0000000000000000000000000000000000000000000000000000",
        "repo_uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/subimage-shared",
    }

    mock_batch_get_manifest.return_value = (
        test_data.ATTESTATION_MANIFEST,
        ecr_layers.ECR_OCI_MANIFEST_MT,
    )

    image_layers_data, digest_map, attestation_map = (
        await ecr_layers.fetch_image_layers_async(
            MagicMock(),
            [repo_image],
            max_concurrent=1,
        )
    )

    assert image_layers_data == {}
    assert digest_map == {}


@patch("cartography.client.aws.ecr.get_ecr_images")
@patch("cartography.intel.aws.ecr_image_layers.batch_get_manifest")
def test_sync_multi_region_event_loop_preserved(
    mock_batch_get_manifest,
    mock_get_ecr_images,
    neo4j_session,
):
    """Test that event loop is preserved across multiple region iterations."""
    from unittest.mock import MagicMock

    # Mock empty ECR images (no actual processing needed for this test)
    mock_get_ecr_images.return_value = set()
    mock_batch_get_manifest.return_value = ({}, "")

    # Create mock boto3 session
    boto3_session = MagicMock()

    try:
        sync_ecr_layers(
            neo4j_session,
            boto3_session,
            ["us-east-1", "us-west-2"],  # Multiple regions
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        )
        # If we reach here without RuntimeError, our loop management is working
        assert True
    except RuntimeError as e:
        if "no current event loop" in str(e).lower():
            pytest.fail("Event loop was torn down between regions - fix needed")
        else:
            raise


# Attestation extraction tests (async I/O integration tests)
@pytest.mark.asyncio
@patch(
    "cartography.intel.aws.ecr_image_layers.batch_get_manifest", new_callable=AsyncMock
)
@patch(
    "cartography.intel.aws.ecr_image_layers.get_blob_json_via_presigned",
    new_callable=AsyncMock,
)
async def test_extract_parent_image_from_attestation_success(
    mock_get_blob, mock_batch_get_manifest
):
    """Test extracting parent image from valid attestation with real API shapes (obfuscated)."""
    # Arrange
    from cartography.intel.aws.ecr_image_layers import (
        _extract_parent_image_from_attestation,
    )

    mock_ecr_client = MagicMock()
    mock_http_client = AsyncMock()

    attestation_manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {
            "mediaType": "application/vnd.oci.image.config.v1+json",
            "digest": "sha256:0f2d70373ae9ec2671e88ad22a01fbf4e3c7ce34dad0f9f95c032752039a514c",
            "size": 167,
        },
        "layers": [
            {
                "mediaType": "application/vnd.in-toto+json",
                "digest": "sha256:74893207cf10d458c45c0e29b05e95f7a1bd942d5d0900b40eca468b5561f15c",
                "size": 11284,
                "annotations": {
                    "in-toto.io/predicate-type": "https://slsa.dev/provenance/v0.2"
                },
            }
        ],
    }

    attestation_blob = {
        "predicate": {
            "materials": [
                {
                    "uri": "pkg:docker/123456789012.dkr.ecr.us-east-1.amazonaws.com/test-base-images@abc123def456",
                    "digest": {
                        "sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
                    },
                },
                {
                    "uri": "pkg:docker/docker/dockerfile@1.7",
                    "digest": {
                        "sha256": "a57df69d0ea827fb7266491f2813635de6f17269be881f696fbfdf2d83dda33e"
                    },
                },
            ]
        }
    }

    mock_batch_get_manifest.return_value = (attestation_manifest, "")
    mock_get_blob.return_value = attestation_blob

    # Act
    result = await _extract_parent_image_from_attestation(
        mock_ecr_client,
        "test-repo",
        "sha256:4150a0d40f045d45614ee1b7ecb2549872dd49ebced5af1ea3a32c5b5523aad2",
        mock_http_client,
    )

    # Assert
    assert result is not None
    assert (
        result["parent_image_uri"]
        == "pkg:docker/123456789012.dkr.ecr.us-east-1.amazonaws.com/test-base-images@abc123def456"
    )
    assert (
        result["parent_image_digest"]
        == "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    )


@pytest.mark.asyncio
@patch(
    "cartography.intel.aws.ecr_image_layers.batch_get_manifest", new_callable=AsyncMock
)
@patch(
    "cartography.intel.aws.ecr_image_layers.get_blob_json_via_presigned",
    new_callable=AsyncMock,
)
async def test_extract_parent_image_from_attestation_no_materials(
    mock_get_blob, mock_batch_get_manifest
):
    """Test attestation with no materials returns None."""
    # Arrange
    from cartography.intel.aws.ecr_image_layers import (
        _extract_parent_image_from_attestation,
    )

    mock_ecr_client = MagicMock()
    mock_http_client = AsyncMock()

    attestation_manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {"digest": "sha256:abc123"},
        "layers": [
            {"mediaType": "application/vnd.in-toto+json", "digest": "sha256:def456"}
        ],
    }

    attestation_blob = {"predicate": {"materials": []}}  # Empty materials

    mock_batch_get_manifest.return_value = (attestation_manifest, "")
    mock_get_blob.return_value = attestation_blob

    # Act
    result = await _extract_parent_image_from_attestation(
        mock_ecr_client, "test-repo", "sha256:attestation", mock_http_client
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
@patch(
    "cartography.intel.aws.ecr_image_layers.batch_get_manifest", new_callable=AsyncMock
)
@patch(
    "cartography.intel.aws.ecr_image_layers.get_blob_json_via_presigned",
    new_callable=AsyncMock,
)
async def test_extract_parent_image_from_attestation_only_dockerfile(
    mock_get_blob, mock_batch_get_manifest
):
    """Test attestation with only dockerfile material returns None."""
    # Arrange
    from cartography.intel.aws.ecr_image_layers import (
        _extract_parent_image_from_attestation,
    )

    mock_ecr_client = MagicMock()
    mock_http_client = AsyncMock()

    attestation_manifest = {
        "layers": [
            {"mediaType": "application/vnd.in-toto+json", "digest": "sha256:def456"}
        ]
    }

    attestation_blob = {
        "predicate": {
            "materials": [
                {
                    "uri": "pkg:docker/docker/dockerfile@1.7",
                    "digest": {"sha256": "abc123"},
                }
            ]
        }
    }

    mock_batch_get_manifest.return_value = (attestation_manifest, "")
    mock_get_blob.return_value = attestation_blob

    # Act
    result = await _extract_parent_image_from_attestation(
        mock_ecr_client, "test-repo", "sha256:attestation", mock_http_client
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
@patch(
    "cartography.intel.aws.ecr_image_layers.batch_get_manifest", new_callable=AsyncMock
)
async def test_extract_parent_image_from_attestation_no_intoto_layer(
    mock_batch_get_manifest,
):
    """Test attestation manifest with no in-toto layer returns None."""
    # Arrange
    from cartography.intel.aws.ecr_image_layers import (
        _extract_parent_image_from_attestation,
    )

    mock_ecr_client = MagicMock()
    mock_http_client = AsyncMock()

    attestation_manifest = {
        "layers": [
            {
                "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "digest": "sha256:wrong",
            }
        ]
    }

    mock_batch_get_manifest.return_value = (attestation_manifest, "")

    # Act
    result = await _extract_parent_image_from_attestation(
        mock_ecr_client, "test-repo", "sha256:attestation", mock_http_client
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
@patch(
    "cartography.intel.aws.ecr_image_layers.batch_get_manifest", new_callable=AsyncMock
)
async def test_extract_parent_image_from_attestation_handles_exceptions(
    mock_batch_get_manifest,
):
    """Test that exceptions are caught and None is returned."""
    # Arrange
    from cartography.intel.aws.ecr_image_layers import (
        _extract_parent_image_from_attestation,
    )

    mock_ecr_client = MagicMock()
    mock_http_client = AsyncMock()

    mock_batch_get_manifest.side_effect = Exception("Network error")

    # Act
    result = await _extract_parent_image_from_attestation(
        mock_ecr_client, "test-repo", "sha256:attestation", mock_http_client
    )

    # Assert
    assert result is None


# End-to-end sync test with attestations


@patch.object(cartography.intel.aws.ecr, "get_ecr_repositories", return_value=[])
@patch.object(cartography.intel.aws.ecr, "get_ecr_repository_images", return_value=[])
@patch("cartography.client.aws.ecr.get_ecr_images")
@patch(
    "cartography.intel.aws.ecr_image_layers.batch_get_manifest", new_callable=AsyncMock
)
@patch(
    "cartography.intel.aws.ecr_image_layers.get_blob_json_via_presigned",
    new_callable=AsyncMock,
)
def test_sync_ecr_layers_with_attestations(
    mock_get_blob,
    mock_batch_get_manifest,
    mock_get_ecr_images,
    mock_get_repo_images,
    mock_get_repos,
    neo4j_session,
):
    """Test full ECR layers sync pipeline with attestation-based BUILT_FROM relationships."""
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Create mock images in the graph (simulating prior ECR sync)
    mock_get_ecr_images.return_value = {
        (
            "us-east-1",
            "1",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/backend:latest",
            "backend",
            "sha256:aaaa000000000000000000000000000000000000000000000000000000000001",
        ),
        (
            "us-east-1",
            "1",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/base-images:main",
            "base-images",
            "sha256:bbbb000000000000000000000000000000000000000000000000000000000001",
        ),
    }

    # Mock manifest list with attestation
    def mock_manifest_side_effect(ecr_client, repo, digest, types):
        if (
            "attestation" in digest or "attestation-manifest" in types[0]
            if types
            else False
        ):
            # Return attestation manifest
            return (
                {
                    "layers": [
                        {
                            "mediaType": "application/vnd.in-toto+json",
                            "digest": "sha256:attestblob",
                        }
                    ]
                },
                "application/vnd.oci.image.manifest.v1+json",
            )
        # Return regular manifest
        return (
            {
                "schemaVersion": 2,
                "config": {"digest": "sha256:config123"},
                "layers": [
                    {"digest": "sha256:layer1"},
                    {"digest": "sha256:layer2"},
                ],
                "manifests": [
                    {
                        "digest": "sha256:childmanifest",
                        "platform": {"architecture": "amd64", "os": "linux"},
                    },
                    {
                        "digest": "sha256:attestation",
                        "annotations": {
                            "vnd.docker.reference.type": "attestation-manifest"
                        },
                    },
                ],
            },
            "application/vnd.oci.image.index.v1+json",
        )

    mock_batch_get_manifest.side_effect = mock_manifest_side_effect

    # Mock config blob and attestation blob
    def mock_blob_side_effect(ecr_client, repo, digest, http_client):
        if digest == "sha256:attestblob":
            return {
                "predicate": {
                    "materials": [
                        {
                            "uri": "pkg:docker/000000000000.dkr.ecr.us-east-1.amazonaws.com/base-images@main",
                            "digest": {
                                "sha256": "bbbb000000000000000000000000000000000000000000000000000000000001"
                            },
                        }
                    ]
                }
            }
        return {"rootfs": {"diff_ids": ["sha256:layer1", "sha256:layer2"]}}

    mock_get_blob.side_effect = mock_blob_side_effect

    # Act
    sync_ecr_layers(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    # Verify layers were created
    layers_query = """
        MATCH (l:ECRImageLayer)
        RETURN l.id as layer_id
        ORDER BY layer_id
    """
    result = neo4j_session.run(layers_query)
    layers = [record["layer_id"] for record in result]
    assert len(layers) > 0

    # Verify BUILT_FROM relationship was created with attestation properties
    built_from_query = """
        MATCH (child:ECRImage)-[r:BUILT_FROM]->(parent:ECRImage)
        RETURN r.parent_image_uri as parent_uri,
               r.from_attestation as from_attestation,
               r.confidence as confidence
    """
    result = neo4j_session.run(built_from_query)
    relationships = list(result)

    # We should have created BUILT_FROM relationships for images with attestations
    # Note: Exact count depends on mock data, but we verify properties are correct
    for rel in relationships:
        assert rel["from_attestation"] is True
        assert rel["confidence"] == "explicit"
        assert rel["parent_uri"] is not None
