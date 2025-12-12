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
    ][:2],
)
@patch("cartography.intel.aws.ecr_image_layers.fetch_image_layers_async")
@patch("cartography.client.aws.ecr.get_ecr_images")
def test_sync_built_from_relationship(
    mock_get_ecr_images,
    mock_fetch_layers,
    mock_get_repo_images,
    mock_get_repos,
    neo4j_session,
):
    """Test that BUILT_FROM relationship is created between ECRImage nodes."""
    parent_digest = (
        "sha256:0000000000000000000000000000000000000000000000000000000000000000"
    )
    child_digest = (
        "sha256:0000000000000000000000000000000000000000000000000000000000000001"
    )

    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    cartography.intel.aws.ecr.sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    mock_get_ecr_images.return_value = {
        (
            "us-east-1",
            "1",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1",
            "example-repository",
            parent_digest,
        ),
        (
            "us-east-1",
            "2",
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:latest",
            "example-repository",
            child_digest,
        ),
    }

    mock_fetch_layers.return_value = (
        {
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1": {
                "linux/amd64": test_data.SAMPLE_CONFIG_BLOB["rootfs"]["diff_ids"]
            },
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:latest": {
                "linux/amd64": test_data.SAMPLE_CONFIG_BLOB["rootfs"]["diff_ids"]
            },
        },
        {
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1": parent_digest,
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:latest": child_digest,
        },
        {
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:latest": {
                "parent_image_uri": "pkg:docker/000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository@1",
                "parent_image_digest": parent_digest,
            }
        },
    )

    sync_ecr_layers(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_rels(
        neo4j_session,
        "ECRImage",
        "id",
        "ECRImage",
        "id",
        "BUILT_FROM",
        rel_direction_right=True,
    ) >= {(child_digest, parent_digest)}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "parent_uri,parent_digest",
    [
        (
            "pkg:docker/123456789012.dkr.ecr.us-east-1.amazonaws.com/base-image@v1.0",
            "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        ),
        (
            "pkg:oci/myregistry.azurecr.io/base-image@v1.0",
            "sha256:abc123def456",
        ),
        (
            "oci://harbor.example.com/library/alpine@sha256:xyz789",
            "sha256:xyz789abc",
        ),
    ],
)
async def test_extract_parent_image_from_attestation_uri_schemes(
    parent_uri, parent_digest
):
    """Test extracting base image from attestation with various URI schemes."""
    # Arrange
    mock_ecr_client = MagicMock()
    mock_http_client = AsyncMock()

    attestation_manifest = (
        {
            "layers": [
                {"mediaType": "application/vnd.in-toto+json", "digest": "sha256:def456"}
            ]
        },
        "application/vnd.oci.image.manifest.v1+json",
    )

    attestation_blob = {
        "predicate": {
            "materials": [
                {
                    "uri": parent_uri,
                    "digest": {"sha256": parent_digest.removeprefix("sha256:")},
                },
            ]
        }
    }

    original_batch_get_manifest = ecr_layers.batch_get_manifest
    original_get_blob = ecr_layers.get_blob_json_via_presigned

    ecr_layers.batch_get_manifest = AsyncMock(return_value=attestation_manifest)
    ecr_layers.get_blob_json_via_presigned = AsyncMock(return_value=attestation_blob)

    try:
        # Act
        result = await ecr_layers._extract_parent_image_from_attestation(
            mock_ecr_client, "test-repo", "sha256:attestation", mock_http_client
        )

        # Assert
        assert result is not None
        assert result["parent_image_uri"] == parent_uri
        assert result["parent_image_digest"] == parent_digest
    finally:
        ecr_layers.batch_get_manifest = original_batch_get_manifest
        ecr_layers.get_blob_json_via_presigned = original_get_blob


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
        "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb": (
            test_data.MULTI_ARCH_AMD64_MANIFEST,
            ecr_layers.ECR_OCI_MANIFEST_MT,
        ),
        "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc": (
            test_data.MULTI_ARCH_ARM64_MANIFEST,
            ecr_layers.ECR_OCI_MANIFEST_MT,
        ),
        "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd": (
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
            # Attestation blob lookup
            "sha256:a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456": test_data.SLSA_PROVENANCE_BLOB,
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

    # Verify platform layers are extracted
    assert image_layers_data == {
        repo_image["uri"]: {
            "linux/amd64": test_data.MULTI_ARCH_AMD64_CONFIG["rootfs"]["diff_ids"],
            "linux/arm64/v8": test_data.MULTI_ARCH_ARM64_CONFIG["rootfs"]["diff_ids"],
        }
    }

    # Verify digest_map includes manifest list and child images
    assert repo_image["uri"] in digest_map
    assert digest_map[repo_image["uri"]] == repo_image["imageDigest"]

    # Verify attestation data is extracted and mapped to child AMD64 image
    # The attestation in MULTI_ARCH_INDEX attests to the AMD64 image (line 108 of test_data)
    expected_child_uri = f"000000000000.dkr.ecr.us-east-1.amazonaws.com/subimage-shared@{test_data.MANIFEST_LIST_AMD64_DIGEST}"
    assert (
        expected_child_uri in attestation_map
    ), "Attestation data should be mapped to child image!"
    assert (
        attestation_map[expected_child_uri]["parent_image_digest"]
        == "sha256:parent1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    )
    # Verify child digest is in digest_map too
    assert digest_map[expected_child_uri] == test_data.MANIFEST_LIST_AMD64_DIGEST


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


@patch.object(
    cartography.intel.aws.ecr,
    "get_ecr_repositories",
    return_value=[
        {
            "repositoryArn": "arn:aws:ecr:us-east-1:000000000000:repository/multi-arch-repository",
            "registryId": "000000000000",
            "repositoryName": "multi-arch-repository",
            "repositoryUri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository",
            "createdAt": test_data.DESCRIBE_REPOSITORIES["repositories"][0][
                "createdAt"
            ],
        }
    ],
)
@patch("cartography.intel.aws.ecr_image_layers.fetch_image_layers_async")
def test_sync_layers_preserves_multi_arch_image_properties(
    mock_fetch_layers,
    mock_get_repos,
    neo4j_session,
):
    """
    Regression test for bug where ecr_image_layers sync would overwrite ECRImage properties to NULL.

    This test ensures that when layer sync runs after ECR sync, it preserves the type, architecture,
    os, variant, and other fields that were set during the initial ECR sync for multi-arch images.
    """
    # Clean up from previous tests
    neo4j_session.run("MATCH (n) DETACH DELETE n;")

    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    mock_client = MagicMock()

    # Mock list_images paginator
    mock_list_paginator = MagicMock()
    mock_list_paginator.paginate.return_value = [
        {
            "imageIds": [
                {
                    "imageDigest": test_data.MANIFEST_LIST_DIGEST,
                    "imageTag": "v1.0",
                }
            ]
        }
    ]

    # Mock describe_images paginator
    mock_describe_paginator = MagicMock()
    mock_describe_paginator.paginate.return_value = [
        {"imageDetails": [test_data.MULTI_ARCH_IMAGE_DETAILS]}
    ]

    # Configure get_paginator
    def get_paginator(name):
        if name == "list_images":
            return mock_list_paginator
        elif name == "describe_images":
            return mock_describe_paginator
        raise ValueError(f"Unexpected paginator: {name}")

    mock_client.get_paginator = get_paginator
    mock_client.batch_get_image.return_value = (
        test_data.BATCH_GET_MANIFEST_LIST_RESPONSE
    )
    boto3_session.client.return_value = mock_client

    # Act 1: Run ECR sync to populate ECRImage nodes with multi-arch properties
    cartography.intel.aws.ecr.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert 1: Verify ECRImage nodes have type, architecture, os, variant set
    assert check_nodes(
        neo4j_session, "ECRImage", ["digest", "type", "architecture"]
    ) == {
        (test_data.MANIFEST_LIST_DIGEST, "manifest_list", None),
        (test_data.MANIFEST_LIST_AMD64_DIGEST, "image", "amd64"),
        (test_data.MANIFEST_LIST_ARM64_DIGEST, "image", "arm64"),
        (test_data.MANIFEST_LIST_ATTESTATION_DIGEST, "attestation", "unknown"),
    }

    # Act 2: Run ECR layers sync
    # Mock fetch_image_layers_async to return layer data for platform-specific images only
    # (NOT manifest list or attestations - they're filtered out before fetching)
    mock_fetch_layers.return_value = (
        # image_layers_data - keyed by the platform-specific image URIs
        {
            f"000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository@{test_data.MANIFEST_LIST_AMD64_DIGEST}": {
                "linux/amd64": test_data.MULTI_ARCH_AMD64_CONFIG["rootfs"]["diff_ids"],
            },
            f"000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository@{test_data.MANIFEST_LIST_ARM64_DIGEST}": {
                "linux/arm64/v8": test_data.MULTI_ARCH_ARM64_CONFIG["rootfs"][
                    "diff_ids"
                ],
            },
        },
        # image_digest_map
        {
            f"000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository@{test_data.MANIFEST_LIST_AMD64_DIGEST}": test_data.MANIFEST_LIST_AMD64_DIGEST,
            f"000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository@{test_data.MANIFEST_LIST_ARM64_DIGEST}": test_data.MANIFEST_LIST_ARM64_DIGEST,
        },
        # image_attestation_map (empty)
        {},
    )

    sync_ecr_layers(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert 2: Verify ECRImage properties are PRESERVED after layer sync (not overwritten to NULL)
    assert check_nodes(
        neo4j_session, "ECRImage", ["digest", "type", "architecture"]
    ) == {
        (test_data.MANIFEST_LIST_DIGEST, "manifest_list", None),
        (test_data.MANIFEST_LIST_AMD64_DIGEST, "image", "amd64"),
        (test_data.MANIFEST_LIST_ARM64_DIGEST, "image", "arm64"),
        (test_data.MANIFEST_LIST_ATTESTATION_DIGEST, "attestation", "unknown"),
    }, "ECRImage properties were overwritten after layer sync!"

    # Verify layer relationships: only platform images (type="image") should have HAS_LAYER relationships
    # Manifest lists and attestations should NOT have any layer relationships
    has_layer_rels = check_rels(
        neo4j_session,
        "ECRImage",
        "digest",
        "ECRImageLayer",
        "diff_id",
        "HAS_LAYER",
        rel_direction_right=True,
    )

    # Get all ECRImage digests that have HAS_LAYER relationships
    images_with_layers = {img_digest for (img_digest, _) in has_layer_rels}

    # Only AMD64 and ARM64 platform images should have layers
    assert images_with_layers == {
        test_data.MANIFEST_LIST_AMD64_DIGEST,
        test_data.MANIFEST_LIST_ARM64_DIGEST,
    }, "Only platform-specific images should have layer relationships!"

    # Manifest list and attestations should NOT be in this set
    assert test_data.MANIFEST_LIST_DIGEST not in images_with_layers
    assert test_data.MANIFEST_LIST_ATTESTATION_DIGEST not in images_with_layers

    # Verify CONTAINS_IMAGE relationships from manifest list to platform images
    assert check_rels(
        neo4j_session,
        "ECRImage",
        "digest",
        "ECRImage",
        "digest",
        "CONTAINS_IMAGE",
        rel_direction_right=True,
    ) == {
        (test_data.MANIFEST_LIST_DIGEST, test_data.MANIFEST_LIST_AMD64_DIGEST),
        (test_data.MANIFEST_LIST_DIGEST, test_data.MANIFEST_LIST_ARM64_DIGEST),
    }

    # Verify ATTESTS relationships from attestations to images they validate
    attests_rels = check_rels(
        neo4j_session,
        "ECRImage",
        "digest",
        "ECRImage",
        "digest",
        "ATTESTS",
        rel_direction_right=True,
    )
    # Attestation should point to the AMD64 image (as defined in test data)
    assert (
        test_data.MANIFEST_LIST_ATTESTATION_DIGEST,
        test_data.MANIFEST_LIST_AMD64_DIGEST,
    ) in attests_rels
