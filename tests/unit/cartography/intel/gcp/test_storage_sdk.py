from unittest.mock import MagicMock
from unittest.mock import patch

from google.api_core import exceptions

from cartography.intel.gcp import storage


def test_get_gcp_buckets_success():
    """
    Test that get_gcp_buckets correctly maps the SDK object to the dictionary format
    expected by the rest of Cartography.
    """
    # Arrange
    project_id = "test-project"
    credentials = MagicMock()

    # Mock the Bucket object that the SDK returns
    mock_bucket = MagicMock()
    mock_bucket.name = "bucket-1"
    mock_bucket.project_number = 123456789
    mock_bucket.time_created.isoformat.return_value = "2023-01-01T00:00:00"
    mock_bucket.updated.isoformat.return_value = "2023-01-02T00:00:00"
    mock_bucket.metageneration = 1
    mock_bucket.location = "US"
    mock_bucket.location_type = "multi-region"
    mock_bucket.storage_class = "STANDARD"
    # Ensure labels are a dict
    mock_bucket.labels = {"env": "prod"}

    # Mock nested configurations
    mock_bucket.iam_configuration.bucket_policy_only_enabled = True
    mock_bucket.owner = {"entity": "project-owners-123", "entityId": "owners-123"}
    mock_bucket.versioning_enabled = True
    mock_bucket.retention_policy_effective_time.isoformat.return_value = (
        "2023-01-03T00:00:00"
    )
    mock_bucket.retention_period = 3600
    mock_bucket.default_kms_key_name = (
        "projects/test/locations/us/keyRings/ring/cryptoKeys/key"
    )
    mock_bucket.log_bucket = "logs-bucket"
    mock_bucket.requester_pays = False

    # Patch the storage.Client class where it is imported in the code
    with patch("cartography.intel.gcp.storage.storage.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        # The SDK's list_buckets returns an iterator
        mock_client.list_buckets.return_value = [mock_bucket]

        # Act
        result = storage.get_gcp_buckets(project_id, credentials)

    # Assert
    assert "items" in result
    assert len(result["items"]) == 1
    bucket_data = result["items"][0]

    # Verify mappings
    assert bucket_data["id"] == "bucket-1"
    assert bucket_data["name"] == "bucket-1"
    assert bucket_data["kind"] == "storage#bucket"
    # Verify nested fields were flattened/mapped correctly
    assert bucket_data["iamConfiguration"]["bucketPolicyOnly"]["enabled"] is True
    assert bucket_data["versioning"]["enabled"] is True
    assert (
        bucket_data["encryption"]["defaultKmsKeyName"]
        == "projects/test/locations/us/keyRings/ring/cryptoKeys/key"
    )
    assert bucket_data["labels"]["env"] == "prod"


def test_get_gcp_buckets_forbidden():
    """
    Test that the function handles a Forbidden (403) error gracefully by returning an empty dict.
    """
    project_id = "test-project"
    credentials = MagicMock()

    with patch("cartography.intel.gcp.storage.storage.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        # Simulate the SDK raising a Forbidden exception
        mock_client.list_buckets.side_effect = exceptions.Forbidden("Access Denied")

        # Act
        result = storage.get_gcp_buckets(project_id, credentials)

    # Assert
    assert result == {}


def test_get_gcp_buckets_invalid_argument():
    """
    Test that the function handles an InvalidArgument error gracefully by returning an empty dict.
    """
    project_id = "invalid-project"
    credentials = MagicMock()

    with patch("cartography.intel.gcp.storage.storage.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        # Simulate the SDK raising an InvalidArgument exception
        mock_client.list_buckets.side_effect = exceptions.InvalidArgument(
            "Invalid project"
        )

        # Act
        result = storage.get_gcp_buckets(project_id, credentials)

    # Assert
    assert result == {}


def test_get_gcp_buckets_generic_error():
    """
    Test that the function handles unexpected exceptions gracefully.
    """
    project_id = "test-project"
    credentials = MagicMock()

    with patch("cartography.intel.gcp.storage.storage.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.list_buckets.side_effect = Exception("Unexpected Boom")

        # Act
        result = storage.get_gcp_buckets(project_id, credentials)

    # Assert
    assert result == {}


def test_get_gcp_buckets_minimal_bucket():
    """
    Test handling of a bucket with minimal attributes (no optional fields).
    """
    project_id = "test-project"
    credentials = MagicMock()

    # Mock a minimal bucket with only required fields
    mock_bucket = MagicMock()
    mock_bucket.name = "minimal-bucket"
    mock_bucket.project_number = 999999
    mock_bucket.time_created = None
    mock_bucket.updated = None
    mock_bucket.metageneration = 1
    mock_bucket.location = "US-CENTRAL1"
    mock_bucket.location_type = "region"
    mock_bucket.storage_class = "NEARLINE"
    mock_bucket.labels = None
    mock_bucket.iam_configuration = None
    mock_bucket.versioning_enabled = None
    mock_bucket.retention_policy_effective_time = None
    mock_bucket.default_kms_key_name = None
    mock_bucket.requester_pays = None

    # Configure hasattr checks
    mock_bucket.owner = None
    mock_bucket.log_bucket = None

    with patch("cartography.intel.gcp.storage.storage.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.list_buckets.return_value = [mock_bucket]

        # Act
        result = storage.get_gcp_buckets(project_id, credentials)

    # Assert
    assert "items" in result
    assert len(result["items"]) == 1
    bucket_data = result["items"][0]

    # Verify basic fields are present
    assert bucket_data["id"] == "minimal-bucket"
    assert bucket_data["name"] == "minimal-bucket"
    assert bucket_data["storageClass"] == "NEARLINE"
    # Verify optional fields are not present or empty
    assert bucket_data["labels"] == {}
    assert bucket_data["timeCreated"] is None
