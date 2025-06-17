import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.trivy import _get_intersection
from cartography.intel.trivy import sync_trivy_aws_ecr_from_s3
from cartography.intel.trivy.scanner import get_json_files_in_s3
from cartography.intel.trivy.scanner import read_scan_results_from_s3
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


@patch("boto3.Session")
def test_read_scan_results_from_s3_with_results(mock_boto3_session):
    # Arrange
    s3_bucket = "test-bucket"
    image_uri = "123456789012.dkr.ecr.us-east-1.amazonaws.com/test-repo:latest"
    s3_object_key = f"{image_uri}.json"

    mock_scan_data = {
        "Results": [
            {
                "Target": "test-image",
                "Vulnerabilities": [
                    {"VulnerabilityID": "CVE-2023-1234", "Severity": "HIGH"}
                ],
            }
        ]
    }

    mock_response_body = MagicMock()
    mock_response_body.read.return_value.decode.return_value = json.dumps(
        mock_scan_data
    )
    mock_boto3_session.return_value.client.return_value.get_object.return_value = {
        "Body": mock_response_body
    }

    # Act
    results, image_digest = read_scan_results_from_s3(
        mock_boto3_session.return_value, s3_bucket, s3_object_key, image_uri
    )

    # Assert
    assert len(results) == 1
    assert results[0]["Target"] == "test-image"
    assert len(results[0]["Vulnerabilities"]) == 1
    assert results[0]["Vulnerabilities"][0]["VulnerabilityID"] == "CVE-2023-1234"
    assert image_digest is None  # No image digest in the mock data

    mock_boto3_session.return_value.client.assert_called_once_with("s3")
    mock_boto3_session.return_value.client.return_value.get_object.assert_called_once_with(
        Bucket=s3_bucket, Key=s3_object_key
    )


@patch("boto3.Session")
def test_read_scan_results_from_s3_empty_results(mock_boto3_session):
    # Arrange
    s3_bucket = "test-bucket"
    image_uri = "123456789012.dkr.ecr.us-west-2.amazonaws.com/my-app:v1.2.3"
    s3_object_key = f"{image_uri}.json"

    mock_scan_data = {"Results": []}

    mock_response_body = MagicMock()
    mock_response_body.read.return_value.decode.return_value = json.dumps(
        mock_scan_data
    )
    mock_boto3_session.return_value.client.return_value.get_object.return_value = {
        "Body": mock_response_body
    }

    # Act
    results, image_digest = read_scan_results_from_s3(
        mock_boto3_session.return_value, s3_bucket, s3_object_key, image_uri
    )

    # Assert
    assert results == []
    assert image_digest is None

    mock_boto3_session.return_value.client.assert_called_once_with("s3")
    mock_boto3_session.return_value.client.return_value.get_object.assert_called_once_with(
        Bucket=s3_bucket, Key=s3_object_key
    )


@patch("boto3.Session")
def test_read_scan_results_from_s3_null_results(mock_boto3_session):
    # Arrange
    s3_bucket = "test-bucket"
    image_uri = (
        "987654321098.dkr.ecr.eu-west-1.amazonaws.com/backend-service:sha256-abcd1234"
    )
    s3_object_key = f"{image_uri}.json"

    mock_scan_data = {"Results": None}

    mock_response_body = MagicMock()
    mock_response_body.read.return_value.decode.return_value = json.dumps(
        mock_scan_data
    )
    mock_boto3_session.return_value.client.return_value.get_object.return_value = {
        "Body": mock_response_body
    }

    # Act
    results, image_digest = read_scan_results_from_s3(
        mock_boto3_session.return_value, s3_bucket, s3_object_key, image_uri
    )

    # Assert
    assert results == []
    assert image_digest is None

    mock_boto3_session.return_value.client.assert_called_once_with("s3")
    mock_boto3_session.return_value.client.return_value.get_object.assert_called_once_with(
        Bucket=s3_bucket, Key=s3_object_key
    )


@patch("boto3.Session")
def test_read_scan_results_from_s3_missing_results_key(mock_boto3_session):
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

    # Act
    results, image_digest = read_scan_results_from_s3(
        mock_boto3_session.return_value, s3_bucket, s3_object_key, image_uri
    )

    # Assert
    assert results == []
    assert image_digest is None

    mock_boto3_session.return_value.client.assert_called_once_with("s3")
    mock_boto3_session.return_value.client.return_value.get_object.assert_called_once_with(
        Bucket=s3_bucket, Key=s3_object_key
    )


@patch("boto3.Session")
def test_read_scan_results_from_s3_s3_error(mock_boto3_session):
    # Arrange
    s3_bucket = "test-bucket"
    image_uri = "111222333444.dkr.ecr.ca-central-1.amazonaws.com/frontend:v2.0.0"
    s3_object_key = f"{image_uri}.json"

    from botocore.exceptions import ClientError

    mock_boto3_session.return_value.client.return_value.get_object.side_effect = (
        ClientError(
            error_response={"Error": {"Code": "NoSuchKey", "Message": "Key not found"}},
            operation_name="GetObject",
        )
    )

    # Act & Assert
    with pytest.raises(ClientError):
        read_scan_results_from_s3(
            mock_boto3_session.return_value, s3_bucket, s3_object_key, image_uri
        )


@patch("boto3.Session")
def test_read_scan_results_from_s3_invalid_json(mock_boto3_session):
    # Arrange
    s3_bucket = "test-bucket"
    image_uri = (
        "999888777666.dkr.ecr.us-east-2.amazonaws.com/data-processor:sha256-xyz789"
    )
    s3_object_key = f"{image_uri}.json"

    mock_response_body = MagicMock()
    mock_response_body.read.return_value.decode.return_value = "invalid json content"
    mock_boto3_session.return_value.client.return_value.get_object.return_value = {
        "Body": mock_response_body
    }

    # Act & Assert
    with pytest.raises(json.JSONDecodeError):
        read_scan_results_from_s3(
            mock_boto3_session.return_value, s3_bucket, s3_object_key, image_uri
        )


@patch("cartography.intel.trivy.scanner.load_scan_fixes")
@patch("cartography.intel.trivy.scanner.load_scan_packages")
@patch("cartography.intel.trivy.scanner.load_scan_vulns")
@patch("cartography.intel.trivy.scanner.transform_scan_results")
@patch("cartography.intel.trivy.scanner.read_scan_results_from_s3")
def test_sync_single_image_from_s3_success(
    mock_read_scan_results,
    mock_transform_scan_results,
    mock_load_scan_vulns,
    mock_load_scan_packages,
    mock_load_scan_fixes,
):
    # Arrange
    mock_neo4j_session = MagicMock()
    mock_boto3_session = MagicMock()

    image_uri = "123456789012.dkr.ecr.us-east-1.amazonaws.com/test-app:v1.2.3"
    update_tag = 12345
    s3_bucket = "trivy-scan-results"
    s3_object_key = f"{image_uri}.json"

    # Mock scan results from S3
    mock_scan_results = [
        {
            "Target": "test-app",
            "Vulnerabilities": [
                {"VulnerabilityID": "CVE-2023-1234", "Severity": "HIGH"}
            ],
        }
    ]
    mock_read_scan_results.return_value = (mock_scan_results, "sha256:abcd1234efgh5678")

    # Mock transformation results
    mock_findings = [{"finding_id": "CVE-2023-1234", "severity": "HIGH"}]
    mock_packages = [{"package_name": "test-package", "version": "1.0.0"}]
    mock_fixes = [{"fix_id": "fix-123", "package": "test-package"}]
    mock_transform_scan_results.return_value = (
        mock_findings,
        mock_packages,
        mock_fixes,
    )

    # Act
    sync_single_image_from_s3(
        mock_neo4j_session,
        image_uri,
        update_tag,
        s3_bucket,
        s3_object_key,
        mock_boto3_session,
    )

    # Assert
    mock_read_scan_results.assert_called_once_with(
        mock_boto3_session,
        s3_bucket,
        s3_object_key,
        image_uri,
    )

    mock_transform_scan_results.assert_called_once_with(
        mock_scan_results,
        "sha256:abcd1234efgh5678",
    )

    mock_load_scan_vulns.assert_called_once_with(
        mock_neo4j_session,
        mock_findings,
        update_tag=update_tag,
    )

    mock_load_scan_packages.assert_called_once_with(
        mock_neo4j_session,
        mock_packages,
        update_tag=update_tag,
    )

    mock_load_scan_fixes.assert_called_once_with(
        mock_neo4j_session,
        mock_fixes,
        update_tag=update_tag,
    )


@patch("cartography.intel.trivy.scanner.read_scan_results_from_s3")
def test_sync_single_image_from_s3_read_error(mock_read_scan_results):
    # Arrange
    mock_neo4j_session = MagicMock()
    mock_boto3_session = MagicMock()

    image_uri = "987654321098.dkr.ecr.eu-west-1.amazonaws.com/backend:latest"
    update_tag = 67890
    s3_bucket = "trivy-scan-results"
    s3_object_key = f"{image_uri}.json"

    # Mock S3 read error
    from botocore.exceptions import ClientError

    mock_read_scan_results.side_effect = ClientError(
        error_response={"Error": {"Code": "NoSuchKey", "Message": "Key not found"}},
        operation_name="GetObject",
    )

    # Act & Assert
    with pytest.raises(ClientError):
        sync_single_image_from_s3(
            mock_neo4j_session,
            image_uri,
            update_tag,
            s3_bucket,
            s3_object_key,
            mock_boto3_session,
        )

    mock_read_scan_results.assert_called_once_with(
        mock_boto3_session,
        s3_bucket,
        s3_object_key,
        image_uri,
    )


@patch("cartography.intel.trivy.scanner.load_scan_vulns")
@patch("cartography.intel.trivy.scanner.transform_scan_results")
@patch("cartography.intel.trivy.scanner.read_scan_results_from_s3")
def test_sync_single_image_from_s3_transform_error(
    mock_read_scan_results,
    mock_transform_scan_results,
    mock_load_scan_vulns,
):
    # Arrange
    mock_neo4j_session = MagicMock()
    mock_boto3_session = MagicMock()

    image_uri = "555666777888.dkr.ecr.ap-southeast-2.amazonaws.com/worker:sha256-def456"
    update_tag = 11111
    s3_bucket = "trivy-scan-results"
    s3_object_key = f"{image_uri}.json"

    # Mock successful S3 read
    mock_scan_results = [{"Target": "worker", "Vulnerabilities": []}]
    mock_read_scan_results.return_value = (mock_scan_results, "sha256:def456ghi789")

    # Mock transformation error
    mock_transform_scan_results.side_effect = KeyError("Missing required field")

    # Act & Assert
    with pytest.raises(KeyError):
        sync_single_image_from_s3(
            mock_neo4j_session,
            image_uri,
            update_tag,
            s3_bucket,
            s3_object_key,
            mock_boto3_session,
        )

    mock_read_scan_results.assert_called_once()
    mock_transform_scan_results.assert_called_once_with(
        mock_scan_results,
        "sha256:def456ghi789",
    )
    mock_load_scan_vulns.assert_not_called()


@patch("cartography.intel.trivy.scanner.load_scan_vulns")
@patch("cartography.intel.trivy.scanner.load_scan_packages")
@patch("cartography.intel.trivy.scanner.transform_scan_results")
@patch("cartography.intel.trivy.scanner.read_scan_results_from_s3")
def test_sync_single_image_from_s3_load_error(
    mock_read_scan_results,
    mock_transform_scan_results,
    mock_load_scan_packages,
    mock_load_scan_vulns,
):
    # Arrange
    mock_neo4j_session = MagicMock()
    mock_boto3_session = MagicMock()

    image_uri = "111222333444.dkr.ecr.ca-central-1.amazonaws.com/api:v3.0.0-beta"
    update_tag = 99999
    s3_bucket = "trivy-scan-results"
    s3_object_key = f"{image_uri}.json"

    # Mock successful S3 read and transform
    mock_scan_results = [{"Target": "api", "Vulnerabilities": []}]
    mock_read_scan_results.return_value = (mock_scan_results, "sha256:beta123abc456")

    mock_findings = []
    mock_packages = []
    mock_fixes = []
    mock_transform_scan_results.return_value = (
        mock_findings,
        mock_packages,
        mock_fixes,
    )

    # Mock load error
    mock_load_scan_vulns.side_effect = Exception("Database connection failed")

    # Act & Assert
    with pytest.raises(Exception, match="Database connection failed"):
        sync_single_image_from_s3(
            mock_neo4j_session,
            image_uri,
            update_tag,
            s3_bucket,
            s3_object_key,
            mock_boto3_session,
        )

    mock_read_scan_results.assert_called_once()
    mock_transform_scan_results.assert_called_once()
    mock_load_scan_vulns.assert_called_once_with(
        mock_neo4j_session,
        mock_findings,
        update_tag=update_tag,
    )
    mock_load_scan_packages.assert_not_called()


def test_get_intersection():
    """Test the _get_intersection function with matching ECR image and S3 scan result."""
    # Arrange
    images_in_graph = {"987654321098.dkr.ecr.us-east-1.amazonaws.com/my-repo:4e380d"}
    json_files = {
        "trivy-scans/987654321098.dkr.ecr.us-east-1.amazonaws.com/my-repo:4e380d.json"
    }
    trivy_s3_prefix = "trivy-scans/"  # Note the trailing slash

    # Act
    result = _get_intersection(images_in_graph, json_files, trivy_s3_prefix)

    # Assert that we retrieve the correct key
    expected = [
        (
            "987654321098.dkr.ecr.us-east-1.amazonaws.com/my-repo:4e380d",
            "trivy-scans/987654321098.dkr.ecr.us-east-1.amazonaws.com/my-repo:4e380d.json",
        )
    ]
    assert result == expected


def test_get_intersection_empty_prefix():
    """Test the _get_intersection function with an empty prefix."""
    # Arrange
    images_in_graph = {"987654321098.dkr.ecr.us-east-1.amazonaws.com/my-repo:4e380d"}
    json_files = {"987654321098.dkr.ecr.us-east-1.amazonaws.com/my-repo:4e380d.json"}
    trivy_s3_prefix = ""  # Empty prefix

    # Act
    result = _get_intersection(images_in_graph, json_files, trivy_s3_prefix)

    # Assert that we retrieve the correct key
    expected = [
        (
            "987654321098.dkr.ecr.us-east-1.amazonaws.com/my-repo:4e380d",
            "987654321098.dkr.ecr.us-east-1.amazonaws.com/my-repo:4e380d.json",
        )
    ]
    assert result == expected


def test_get_intersection_no_matches():
    """Test the _get_intersection function when there are no matching images."""
    # Arrange
    images_in_graph = {"987654321098.dkr.ecr.us-east-1.amazonaws.com/my-repo:4e380d"}
    json_files = {
        "trivy-scans/111111111111.dkr.ecr.us-east-1.amazonaws.com/other-repo:latest.json"
    }
    trivy_s3_prefix = "trivy-scans/"

    # Act
    result = _get_intersection(images_in_graph, json_files, trivy_s3_prefix)

    # Assert that we get an empty list when there are no matches
    assert result == []


@patch("cartography.intel.trivy.get_scan_targets")
@patch("cartography.intel.trivy.scanner.get_json_files_in_s3")
@patch("cartography.intel.trivy._get_intersection")
def test_sync_trivy_aws_ecr_from_s3_no_matches(
    mock_get_intersection,
    mock_get_json_files,
    mock_get_scan_targets,
):
    """Test that sync_trivy_aws_ecr_from_s3 raises an error when no images match."""
    # Arrange
    mock_get_scan_targets.return_value = {
        "987654321098.dkr.ecr.us-east-1.amazonaws.com/my-repo:4e380d"
    }
    mock_get_json_files.return_value = {
        "trivy-scans/111111111111.dkr.ecr.us-east-1.amazonaws.com/other-repo:latest.json"
    }
    mock_get_intersection.return_value = []  # No matches found

    # Act & Assert
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
