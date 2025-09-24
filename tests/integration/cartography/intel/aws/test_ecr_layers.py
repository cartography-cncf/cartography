import json
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ecr as ecr
import tests.data.aws.ecr as test_data
from cartography.intel.aws.ecr import sync as sync_ecr
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

    result = ecr.transform_ecr_image_layers(image_layers_data, image_digest_map)

    # Check that we have 5 unique layers
    assert len(result) == 5

    # Check layer1 is HEAD of both images
    layer1 = next(layer for layer in result if layer["diff_id"] == "sha256:layer1")
    assert set(layer1["head_image_ids"]) == {"sha256:digest1", "sha256:digest2"}
    assert layer1["next_diff_id"] == "sha256:layer2"

    # Check layer3 is TAIL of first image
    layer3 = next(layer for layer in result if layer["diff_id"] == "sha256:layer3")
    assert layer3["tail_image_ids"] == ["sha256:digest1"]
    assert "next_diff_id" not in layer3

    # Check layer5 is TAIL of second image
    layer5 = next(layer for layer in result if layer["diff_id"] == "sha256:layer5")
    assert layer5["tail_image_ids"] == ["sha256:digest2"]
    assert "next_diff_id" not in layer5


def test_parse_image_uri():
    """Test the parse_image_uri function."""
    # Test with tag
    region, repo, ref = ecr.parse_image_uri(
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:latest"
    )
    assert region == "us-east-1"
    assert repo == "example-repository"
    assert ref == "latest"

    # Test with digest
    region, repo, ref = ecr.parse_image_uri(
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository@sha256:abc123"
    )
    assert region == "us-east-1"
    assert repo == "example-repository"
    assert ref == "sha256:abc123"

    # Test without tag or digest (defaults to latest)
    region, repo, ref = ecr.parse_image_uri(
        "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository"
    )
    assert region == "us-east-1"
    assert repo == "example-repository"
    assert ref == "latest"


@patch("cartography.intel.aws.ecr.get_ecr_repositories")
@patch("cartography.intel.aws.ecr.get_ecr_repository_images")
@patch("cartography.intel.aws.ecr.batch_get_manifest")
@patch("cartography.intel.aws.ecr.get_blob_json_via_presigned")
def test_sync_with_layers(
    mock_get_blob,
    mock_batch_get_manifest,
    mock_get_images,
    mock_get_repos,
    neo4j_session,
):
    """Test ECR sync with image layer support."""
    # Mock repository data
    mock_get_repos.return_value = test_data.DESCRIBE_REPOSITORIES["repositories"][:1]

    # Mock image data
    mock_get_images.return_value = [
        {
            "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "imageTag": "1",
            "repositoryName": "example-repository",
            **test_data.DESCRIBE_IMAGES["imageDetails"],
        }
    ]

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

    # Run sync
    sync_ecr(
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
        check_nodes(neo4j_session, "ECRImage", ["id", "region"]) == expected_ecr_images
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
    assert check_nodes(neo4j_session, "ImageLayer", ["id", "region"]) == expected_layers

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


def test_get_image_diff_ids_single_manifest():
    """Test get_image_diff_ids with a single platform manifest."""
    mock_ecr_client = MagicMock()

    # Mock batch_get_image to return single manifest
    mock_ecr_client.batch_get_image.return_value = {
        "images": [
            {
                "imageManifest": json.dumps(test_data.SAMPLE_MANIFEST),
                "imageManifestMediaType": "application/vnd.docker.distribution.manifest.v2+json",
            }
        ]
    }

    # Mock get_download_url_for_layer
    mock_ecr_client.get_download_url_for_layer.return_value = {
        "downloadUrl": "https://example.s3.amazonaws.com/blob"
    }

    # Mock URL fetch to return config blob
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            test_data.SAMPLE_CONFIG_BLOB
        ).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = ecr.get_image_diff_ids(
            mock_ecr_client,
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1",
        )

    assert "linux/amd64" in result
    assert result["linux/amd64"] == test_data.SAMPLE_CONFIG_BLOB["rootfs"]["diff_ids"]


def test_get_image_diff_ids_manifest_list():
    """Test get_image_diff_ids with a multi-arch manifest list."""
    mock_ecr_client = MagicMock()

    # First call returns manifest list
    # Subsequent calls return platform-specific manifests
    mock_ecr_client.batch_get_image.side_effect = [
        {
            "images": [
                {
                    "imageManifest": json.dumps(test_data.SAMPLE_MANIFEST_LIST),
                    "imageManifestMediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
                }
            ]
        },
        # AMD64 manifest
        {
            "images": [
                {
                    "imageManifest": json.dumps(test_data.SAMPLE_MANIFEST),
                    "imageManifestMediaType": "application/vnd.docker.distribution.manifest.v2+json",
                }
            ]
        },
        # ARM64 manifest
        {
            "images": [
                {
                    "imageManifest": json.dumps(test_data.SAMPLE_MANIFEST),
                    "imageManifestMediaType": "application/vnd.docker.distribution.manifest.v2+json",
                }
            ]
        },
    ]

    # Mock get_download_url_for_layer
    mock_ecr_client.get_download_url_for_layer.return_value = {
        "downloadUrl": "https://example.s3.amazonaws.com/blob"
    }

    # Mock URL fetch to return config blob
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            test_data.SAMPLE_CONFIG_BLOB
        ).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = ecr.get_image_diff_ids(
            mock_ecr_client,
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository:1",
        )

    # Should have results for both platforms
    assert "linux/amd64" in result
    assert "linux/arm64/v8" in result
    assert result["linux/amd64"] == test_data.SAMPLE_CONFIG_BLOB["rootfs"]["diff_ids"]
    assert (
        result["linux/arm64/v8"] == test_data.SAMPLE_CONFIG_BLOB["rootfs"]["diff_ids"]
    )
