import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.trivy import sync_trivy_aws_ecr_from_s3
from cartography.intel.trivy.scanner import get_json_files_in_s3
from cartography.intel.trivy.scanner import sync_single_image_from_s3


@patch("boto3.Session")
def test_list_s3_scan_results_basic_match(mock_boto3_session):
    """Test basic S3 object listing with matching ECR images."""
    # Arrange
    mock_boto3_session.return_value.client.return_value.get_paginator.return_value.paginate.return_value = [
        {
            "Contents": [
                {
                    "Key": "scan-results/123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo:latest.json"
                },
                {
                    "Key": "scan-results/123456789012.dkr.ecr.us-west-2.amazonaws.com/other-repo:v1.0.json"
                },
                {"Key": "scan-results/some-other-file.txt"},  # Should be ignored
            ]
        }
    ]

    # Act
    result = get_json_files_in_s3(
        s3_bucket="my-bucket",
        s3_prefix="scan-results",
        boto3_session=mock_boto3_session.return_value,
    )

    # Assert
    assert len(result) == 2
    expected_keys = {
        "scan-results/123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo:latest.json",
        "scan-results/123456789012.dkr.ecr.us-west-2.amazonaws.com/other-repo:v1.0.json",
    }
    assert result == expected_keys

    mock_boto3_session.return_value.client.assert_called_once_with("s3")
    mock_boto3_session.return_value.client.return_value.get_paginator.assert_called_once_with(
        "list_objects_v2"
    )
    mock_boto3_session.return_value.client.return_value.get_paginator.return_value.paginate.assert_called_once_with(
        Bucket="my-bucket", Prefix="scan-results"
    )


@patch("boto3.Session")
def test_list_s3_scan_results_no_matches(mock_boto3_session):
    """Test S3 object listing when no ECR images match."""
    # Arrange
    mock_boto3_session.return_value.client.return_value.get_paginator.return_value.paginate.return_value = [
        {
            "Contents": [
                {"Key": "scan-results/some-other-image:latest.json"},
                {"Key": "scan-results/another-image:v1.0.json"},
            ]
        }
    ]

    # Act
    result = get_json_files_in_s3(
        s3_bucket="my-bucket",
        s3_prefix="scan-results",
        boto3_session=mock_boto3_session.return_value,
    )

    # Assert
    assert len(result) == 2
    expected_keys = [
        "scan-results/some-other-image:latest.json",
        "scan-results/another-image:v1.0.json",
    ]
    assert sorted(result) == sorted(expected_keys)

    mock_boto3_session.return_value.client.assert_called_once_with("s3")
    mock_boto3_session.return_value.client.return_value.get_paginator.assert_called_once_with(
        "list_objects_v2"
    )
    mock_boto3_session.return_value.client.return_value.get_paginator.return_value.paginate.assert_called_once_with(
        Bucket="my-bucket", Prefix="scan-results"
    )


@patch("boto3.Session")
def test_list_s3_scan_results_empty_s3_response(mock_boto3_session):
    """Test S3 object listing when S3 bucket is empty."""
    # Arrange
    mock_boto3_session.return_value.client.return_value.get_paginator.return_value.paginate.return_value = [
        {}
    ]  # No Contents key

    # Act
    result = get_json_files_in_s3(
        s3_bucket="my-bucket",
        s3_prefix="scan-results",
        boto3_session=mock_boto3_session.return_value,
    )

    # Assert
    assert len(result) == 0


@patch("boto3.Session")
def test_list_s3_scan_results_with_url_encoding(mock_boto3_session):
    """Test S3 object listing with URL-encoded image URIs."""
    # Arrange
    mock_boto3_session.return_value.client.return_value.get_paginator.return_value.paginate.return_value = [
        {
            "Contents": [
                {
                    "Key": "scan-results/123456789012.dkr.ecr.us-east-1.amazonaws.com%2Fmy-repo%3Alatest.json"
                },
            ]
        }
    ]

    # Act
    result = get_json_files_in_s3(
        s3_bucket="my-bucket",
        s3_prefix="scan-results",
        boto3_session=mock_boto3_session.return_value,
    )

    # Assert
    assert len(result) == 1
    expected_keys = [
        "scan-results/123456789012.dkr.ecr.us-east-1.amazonaws.com%2Fmy-repo%3Alatest.json"
    ]
    assert sorted(result) == sorted(expected_keys)

    mock_boto3_session.return_value.client.assert_called_once_with("s3")
    mock_boto3_session.return_value.client.return_value.get_paginator.assert_called_once_with(
        "list_objects_v2"
    )
    mock_boto3_session.return_value.client.return_value.get_paginator.return_value.paginate.assert_called_once_with(
        Bucket="my-bucket", Prefix="scan-results"
    )


@patch("boto3.Session")
def test_list_s3_scan_results_s3_error(mock_boto3_session):
    """Test S3 object listing when S3 API raises an exception."""
    # Arrange
    mock_boto3_session.return_value.client.return_value.get_paginator.side_effect = (
        Exception("S3 API Error")
    )

    # Act & Assert
    try:
        get_json_files_in_s3(
            s3_bucket="my-bucket",
            s3_prefix="scan-results",
            boto3_session=mock_boto3_session.return_value,
        )
        assert False, "Expected exception was not raised"
    except Exception as e:
        assert str(e) == "S3 API Error"


@patch("cartography.intel.trivy.scanner.sync_single_image")
@patch("boto3.Session")
def test_sync_single_image_from_s3_missing_results_key(
    mock_boto3_session, mock_sync_single_image
):
    # Arrange
    s3_bucket = "test-bucket"
    image_uri = "555666777888.dkr.ecr.ap-southeast-2.amazonaws.com/microservice:latest"
    s3_object_key = f"{image_uri}.json"

    mock_scan_data = {"Metadata": {"ImageID": "test-image"}}

    mock_response_body = MagicMock()
    mock_response_body.read.return_value.decode.return_value = json.dumps(
        mock_scan_data
    )
    mock_boto3_session.return_value.client.return_value.get_object.return_value = {
        "Body": mock_response_body
    }

    # Make sync_single_image raise the error when called
    mock_sync_single_image.side_effect = ValueError(
        "Missing 'Results' key in scan data"
    )

    # Act & Assert
    with pytest.raises(ValueError, match="Missing 'Results' key in scan data"):
        sync_single_image_from_s3(
            MagicMock(),  # neo4j_session
            image_uri,
            12345,  # update_tag
            s3_bucket,
            s3_object_key,
            mock_boto3_session.return_value,
        )


@patch("cartography.intel.trivy.scanner.sync_single_image")
@patch("boto3.Session")
def test_sync_single_image_from_s3_success(
    mock_boto3_session,
    mock_sync_single_image,
):
    # Arrange
    mock_neo4j_session = MagicMock()

    image_uri = "123456789012.dkr.ecr.us-east-1.amazonaws.com/test-app:v1.2.3"
    update_tag = 12345
    s3_bucket = "trivy-scan-results"
    s3_object_key = f"{image_uri}.json"

    # Mock S3 response
    mock_scan_data = {
        "Results": [
            {
                "Target": "test-app",
                "Vulnerabilities": [
                    {"VulnerabilityID": "CVE-2023-1234", "Severity": "HIGH"}
                ],
            }
        ],
        "Metadata": {
            "RepoDigests": [
                f"{image_uri.split(':')[0]}@sha256:abcd1234efgh5678abcd1234efgh5678abcd1234efgh5678abcd1234efgh5678"
            ]
        },
    }

    mock_response_body = MagicMock()
    mock_response_body.read.return_value.decode.return_value = json.dumps(
        mock_scan_data
    )
    mock_boto3_session.return_value.client.return_value.get_object.return_value = {
        "Body": mock_response_body
    }

    # Act
    sync_single_image_from_s3(
        mock_neo4j_session,
        image_uri,
        update_tag,
        s3_bucket,
        s3_object_key,
        mock_boto3_session.return_value,
    )

    # Assert
    mock_boto3_session.return_value.client.assert_called_once_with("s3")
    mock_boto3_session.return_value.client.return_value.get_object.assert_called_once_with(
        Bucket=s3_bucket, Key=s3_object_key
    )

    # Verify sync_single_image was called with the correct data
    mock_sync_single_image.assert_called_once_with(
        mock_neo4j_session,
        mock_scan_data,
        image_uri,
        update_tag,
    )


@patch("boto3.Session")
def test_sync_single_image_from_s3_read_error(mock_boto3_session):
    # Arrange
    mock_neo4j_session = MagicMock()

    image_uri = "987654321098.dkr.ecr.eu-west-1.amazonaws.com/backend:latest"
    update_tag = 67890
    s3_bucket = "trivy-scan-results"
    s3_object_key = f"{image_uri}.json"

    # Mock S3 read error
    from botocore.exceptions import ClientError

    mock_boto3_session.return_value.client.return_value.get_object.side_effect = (
        ClientError(
            error_response={"Error": {"Code": "NoSuchKey", "Message": "Key not found"}},
            operation_name="GetObject",
        )
    )

    # Act & Assert
    with pytest.raises(ClientError):
        sync_single_image_from_s3(
            mock_neo4j_session,
            image_uri,
            update_tag,
            s3_bucket,
            s3_object_key,
            mock_boto3_session.return_value,
        )

    mock_boto3_session.return_value.client.assert_called_once_with("s3")
    mock_boto3_session.return_value.client.return_value.get_object.assert_called_once_with(
        Bucket=s3_bucket, Key=s3_object_key
    )


@patch("cartography.intel.trivy.scanner.sync_single_image")
@patch("boto3.Session")
def test_sync_single_image_from_s3_transform_error(
    mock_boto3_session,
    mock_sync_single_image,
):
    # Arrange
    mock_neo4j_session = MagicMock()

    image_uri = "555666777888.dkr.ecr.ap-southeast-2.amazonaws.com/worker:sha256-def456"
    update_tag = 11111
    s3_bucket = "trivy-scan-results"
    s3_object_key = f"{image_uri}.json"

    # Mock successful S3 read
    mock_scan_data = {
        "Results": [{"Target": "worker", "Vulnerabilities": []}],
        "Metadata": {
            "RepoDigests": [
                f"{image_uri.split(':')[0]}@sha256:def456ghi789def456ghi789def456ghi789def456ghi789def456ghi789def4"
            ]
        },
    }

    mock_response_body = MagicMock()
    mock_response_body.read.return_value.decode.return_value = json.dumps(
        mock_scan_data
    )
    mock_boto3_session.return_value.client.return_value.get_object.return_value = {
        "Body": mock_response_body
    }

    # Mock transformation error in sync_single_image
    mock_sync_single_image.side_effect = KeyError("Missing required field")

    # Act & Assert
    with pytest.raises(KeyError):
        sync_single_image_from_s3(
            mock_neo4j_session,
            image_uri,
            update_tag,
            s3_bucket,
            s3_object_key,
            mock_boto3_session.return_value,
        )

    mock_sync_single_image.assert_called_once()


@patch("cartography.intel.trivy.scanner.sync_single_image")
@patch("boto3.Session")
def test_sync_single_image_from_s3_load_error(
    mock_boto3_session,
    mock_sync_single_image,
):
    # Arrange
    mock_neo4j_session = MagicMock()

    image_uri = "111222333444.dkr.ecr.ca-central-1.amazonaws.com/api:v3.0.0-beta"
    update_tag = 99999
    s3_bucket = "trivy-scan-results"
    s3_object_key = f"{image_uri}.json"

    # Mock successful S3 read
    mock_scan_data = {
        "Results": [{"Target": "api", "Vulnerabilities": []}],
        "Metadata": {
            "RepoDigests": [
                f"{image_uri.split(':')[0]}@sha256:beta123abc456beta123abc456beta123abc456beta123abc456beta123abc456"
            ]
        },
    }

    mock_response_body = MagicMock()
    mock_response_body.read.return_value.decode.return_value = json.dumps(
        mock_scan_data
    )
    mock_boto3_session.return_value.client.return_value.get_object.return_value = {
        "Body": mock_response_body
    }

    # Mock load error in sync_single_image
    mock_sync_single_image.side_effect = Exception("Database connection failed")

    # Act & Assert
    with pytest.raises(Exception, match="Database connection failed"):
        sync_single_image_from_s3(
            mock_neo4j_session,
            image_uri,
            update_tag,
            s3_bucket,
            s3_object_key,
            mock_boto3_session.return_value,
        )

    mock_sync_single_image.assert_called_once()


@patch("cartography.intel.trivy._get_scan_targets_and_aliases")
@patch("cartography.intel.trivy.get_json_files_in_s3")
def test_sync_trivy_aws_ecr_from_s3_no_matches(
    mock_get_json_files,
    mock_get_targets_and_aliases,
):
    """Test that sync_trivy_aws_ecr_from_s3 raises when no JSON files are present."""
    mock_get_targets_and_aliases.return_value = (
        {"987654321098.dkr.ecr.us-east-1.amazonaws.com/my-repo:4e380d"},
        {},
    )
    mock_get_json_files.return_value = set()  # No scan results available

    with pytest.raises(
        ValueError, match="No ECR images with S3 json scan results found"
    ):
        sync_trivy_aws_ecr_from_s3(
            neo4j_session=MagicMock(),
            trivy_s3_bucket="test-bucket",
            trivy_s3_prefix="trivy-scans/",
            update_tag=123,
            common_job_parameters={},
            boto3_session=MagicMock(),
        )


@patch("cartography.intel.trivy.cleanup")
@patch("cartography.intel.trivy.sync_single_image")
@patch("cartography.intel.trivy._get_scan_targets_and_aliases")
@patch("cartography.intel.trivy.get_json_files_in_s3")
@patch("boto3.Session")
def test_sync_trivy_aws_ecr_from_s3_digest_files(
    mock_boto_session,
    mock_get_json_files,
    mock_get_targets_and_aliases,
    mock_sync_single_image,
    mock_cleanup,
):
    """Ensure digest-named files are processed and mapped to the tag URI."""
    display_uri = "123456789012.dkr.ecr.us-west-2.amazonaws.com/app:1.2.3"
    digest_uri = (
        "123456789012.dkr.ecr.us-west-2.amazonaws.com/app@sha256:abcdefabcdefabcdef"
    )

    mock_get_targets_and_aliases.return_value = (
        {display_uri},
        {digest_uri: display_uri},
    )
    mock_get_json_files.return_value = {"trivy-scans/app@sha256abcdef.json"}

    scan_payload = {
        "ArtifactName": digest_uri,
        "Metadata": {
            "RepoDigests": [digest_uri],
            "RepoTags": [],
            "SubImagePlatforms": ["linux/amd64"],
        },
        "Results": [{"Target": "app", "Vulnerabilities": []}],
    }

    body = MagicMock()
    body.read.return_value.decode.return_value = json.dumps(scan_payload)
    mock_boto_session.return_value.client.return_value.get_object.return_value = {
        "Body": body
    }

    sync_trivy_aws_ecr_from_s3(
        neo4j_session=MagicMock(),
        trivy_s3_bucket="test-bucket",
        trivy_s3_prefix="trivy-scans/",
        update_tag=123,
        common_job_parameters={},
        boto3_session=mock_boto_session.return_value,
    )

    mock_sync_single_image.assert_called_once()
    normalized_payload = mock_sync_single_image.call_args[0][1]
    assert normalized_payload["ArtifactName"] == digest_uri
