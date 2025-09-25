import asyncio
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.aws.ecr_image_layers as ecr_layers
import tests.data.aws.ecr as test_data
from cartography.intel.aws.ecr_image_layers import sync as sync_ecr_layers
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789
TEST_REGION = "us-east-1"


def test_transform_ecr_image_layers():
    """Test the transform_ecr_image_layers function."""
    # Sample layer data for testing
    image_layers_data = {
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1": {
            "linux/amd64": [
                "sha256:layer1",
                "sha256:layer2",
                "sha256:layer3",
            ]
        },
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:2": {
            "linux/amd64": [
                "sha256:layer1",  # Shared layer
                "sha256:layer4",
                "sha256:layer5",
            ]
        },
    }

    image_digest_map = {
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1": "sha256:digest1",
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:2": "sha256:digest2",
    }

    layers, memberships = ecr_layers.transform_ecr_image_layers(
        image_layers_data,
        image_digest_map,
    )

    # Check that we have 5 unique layers
    assert len(layers) == 5

    # Check layer1 is HEAD of both images
    layer1 = next(layer for layer in layers if layer["diff_id"] == "sha256:layer1")
    assert not layer1["is_empty"]
    assert set(layer1["head_image_ids"]) == {"sha256:digest1", "sha256:digest2"}
    # Layer1 should have NEXT edges to both layer2 and layer4
    assert set(layer1["next_diff_ids"]) == {"sha256:layer2", "sha256:layer4"}

    # Check layer3 is TAIL of first image
    layer3 = next(layer for layer in layers if layer["diff_id"] == "sha256:layer3")
    assert not layer3["is_empty"]
    assert layer3["tail_image_ids"] == ["sha256:digest1"]
    assert "next_diff_ids" not in layer3

    # Check layer5 is TAIL of second image
    layer5 = next(layer for layer in layers if layer["diff_id"] == "sha256:layer5")
    assert not layer5["is_empty"]
    assert layer5["tail_image_ids"] == ["sha256:digest2"]
    assert "next_diff_ids" not in layer5

    # Membership list should include each layer per image with index information
    expected_memberships = {
        (
            "sha256:digest1",
            (
                "sha256:layer1",
                "sha256:layer2",
                "sha256:layer3",
            ),
        ),
        (
            "sha256:digest2",
            (
                "sha256:layer1",
                "sha256:layer4",
                "sha256:layer5",
            ),
        ),
    }
    membership_tuples = {
        (m["imageDigest"], tuple(m["layer_diff_ids"])) for m in memberships
    }
    assert membership_tuples == expected_memberships


@patch("cartography.client.aws.ecr.get_ecr_images")
@patch("cartography.intel.aws.ecr_image_layers.batch_get_manifest")
@patch("cartography.intel.aws.ecr_image_layers.get_blob_json_via_presigned")
def test_sync_with_layers(
    mock_get_blob,
    mock_batch_get_manifest,
    mock_get_ecr_images,
    neo4j_session,
):
    """Test ECR sync with image layer support using graph-based approach."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # First, create the basic ECR data that would normally be created by 'ecr' module
        from cartography.intel.aws.ecr import load_ecr_repositories
        from cartography.intel.aws.ecr import load_ecr_repository_images

        # Create minimal test data
        mock_repositories = test_data.DESCRIBE_REPOSITORIES["repositories"][:1]
        uri = "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1"
        mock_repo_images = [
            {
                "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
                "imageTag": "1",
                "uri": uri,
                "id": uri,
                "repo_uri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository",
                **test_data.DESCRIBE_IMAGES["imageDetails"],
            }
        ]

        load_ecr_repositories(
            neo4j_session,
            mock_repositories,
            TEST_REGION,
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
        )
        load_ecr_repository_images(
            neo4j_session,
            mock_repo_images,
            TEST_REGION,
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
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

        # Run sync with layer support
        sync_ecr_layers(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        )

        # Check that ECRImage nodes were created
        expected_ecr_images = {
            (
                "sha256:0000000000000000000000000000000000000000000000000000000000000000",
                TEST_REGION,
            ),
        }
        assert (
            check_nodes(neo4j_session, "ECRImage", ["id", "region"])
            == expected_ecr_images
        )

        # Check that ImageLayer nodes were created
        expected_layers = {
            (
                "sha256:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
                TEST_REGION,
            ),
            (
                "sha256:fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
                TEST_REGION,
            ),
            (
                "sha256:4ac5bb3f45ba451e817df5f30b950f6eb32145e00ba5f134973810881fde7ac0",
                TEST_REGION,
            ),
        }
        assert (
            check_nodes(neo4j_session, "ImageLayer", ["id", "region"])
            == expected_layers
        )

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
                "ImageLayer",
                "id",
                "ImageLayer",
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
                "ImageLayer",
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
            MATCH (img:ECRImage {id: $digest})-[:HEAD]->(head:ImageLayer)
            MATCH (img)-[:TAIL]->(tail:ImageLayer)
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
    finally:
        loop.close()
        asyncio.set_event_loop(None)


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

    layers, memberships = ecr_layers.transform_ecr_image_layers(
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

    image_layers_data, digest_map = await ecr_layers.fetch_image_layers_async(
        MagicMock(),
        [repo_image],
        max_concurrent=1,
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

    image_layers_data, digest_map = await ecr_layers.fetch_image_layers_async(
        MagicMock(),
        [repo_image],
        max_concurrent=1,
    )

    assert image_layers_data == {}
    assert digest_map == {}
