import datetime
from datetime import timezone
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.aws.s3_objects
from cartography.intel.aws.s3_objects import sync
from cartography.intel.aws.s3_objects import transform_s3_objects
from tests.data.aws.s3object import LIST_S3_OBJECTS
from tests.data.aws.s3object import SINGLE_GLACIER_OBJECT
from tests.data.aws.s3object import SINGLE_OBJECT_WITH_OWNER
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789
TEST_BUCKET_NAME = "test-bucket"
TEST_BUCKET_ARN = "arn:aws:s3:::test-bucket"


@pytest.fixture
def setup_s3_bucket(neo4j_session):
    """Setup test S3 bucket in Neo4j."""
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    neo4j_session.run(
        """
        MERGE (b:S3Bucket{id: $bucket_arn})
        SET b.name = $bucket_name,
            b.region = $region,
            b.lastupdated = $update_tag
        WITH b
        MATCH (a:AWSAccount{id: $account_id})
        MERGE (a)-[r:RESOURCE]->(b)
        SET r.lastupdated = $update_tag
        """,
        bucket_arn=TEST_BUCKET_ARN,
        bucket_name=TEST_BUCKET_NAME,
        region=TEST_REGION,
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    neo4j_session.run("MATCH (o:S3Object) DETACH DELETE o")


def _mock_transform_objects(objects):
    """Transform test objects using actual transform function."""
    return transform_s3_objects(
        objects, TEST_BUCKET_NAME, TEST_BUCKET_ARN, TEST_REGION, TEST_ACCOUNT_ID
    )


@patch.object(
    cartography.intel.aws.s3_objects,
    "get_s3_object_data",
    return_value=_mock_transform_objects(LIST_S3_OBJECTS),
)
def test_sync_s3_objects(mock_get_data, neo4j_session, setup_s3_bucket):
    """Test basic S3 object sync functionality."""
    boto3_session = MagicMock()

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(neo4j_session, "S3Object", ["key", "size", "storage_class"]) == {
        ("documents/report.pdf", 1024000, "STANDARD"),
        ("images/logo.png", 50000, "STANDARD_IA"),
        ("archive/old-data.zip", 5000000, "GLACIER"),
        ("deleted/file.txt", 0, "STANDARD"),
    }

    assert check_rels(
        neo4j_session,
        "S3Bucket",
        "id",
        "S3Object",
        "key",
        "STORES",
        rel_direction_right=True,
    ) == {
        (TEST_BUCKET_ARN, "documents/report.pdf"),
        (TEST_BUCKET_ARN, "images/logo.png"),
        (TEST_BUCKET_ARN, "archive/old-data.zip"),
        (TEST_BUCKET_ARN, "deleted/file.txt"),
    }


@patch.object(
    cartography.intel.aws.s3_objects,
    "get_s3_object_data",
    return_value=_mock_transform_objects(SINGLE_GLACIER_OBJECT),
)
def test_sync_s3_objects_glacier_restore(mock_get_data, neo4j_session, setup_s3_bucket):
    """Test Glacier object with restore status."""
    boto3_session = MagicMock()

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    result = neo4j_session.run(
        """
        MATCH (o:S3Object{key: 'archive/old-data.zip'})
        RETURN o.storage_class as storage_class,
               o.is_restore_in_progress as is_restore_in_progress,
               o.restore_expiry_date as restore_expiry_date
        """
    ).single()

    assert result["storage_class"] == "GLACIER"
    assert result["is_restore_in_progress"] is True
    assert result["restore_expiry_date"] is not None


@patch.object(
    cartography.intel.aws.s3_objects,
    "get_s3_object_data",
    return_value=_mock_transform_objects(SINGLE_OBJECT_WITH_OWNER),
)
def test_sync_s3_objects_with_owner(mock_get_data, neo4j_session, setup_s3_bucket):
    """Test S3 object with owner information creates AWSPrincipal relationship."""
    boto3_session = MagicMock()

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    result = neo4j_session.run(
        """
        MATCH (o:S3Object{key: 'images/logo.png'})
        RETURN o.owner_id as owner_id, o.owner_display_name as owner_display_name
        """
    ).single()

    assert result["owner_id"] == "owner-id-123"
    assert result["owner_display_name"] == "test-owner"

    owner_result = neo4j_session.run(
        """
        MATCH (p:AWSPrincipal{id: 'owner-id-123'})-[r:OWNS]->(o:S3Object{key: 'images/logo.png'})
        RETURN p.id as id, p.display_name as display_name
        """
    ).single()

    assert owner_result["id"] == "owner-id-123"


@patch.object(
    cartography.intel.aws.s3_objects,
    "get_s3_object_data",
    return_value=[],
)
def test_sync_s3_objects_disabled(mock_get_data, neo4j_session, setup_s3_bucket):
    """Test S3 object sync can be disabled with limit=0."""
    boto3_session = MagicMock()

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_ACCOUNT_ID,
            "aws_s3_object_sync_limit": 0,
        },
    )

    mock_get_data.assert_called_once_with(
        neo4j_session, boto3_session, TEST_ACCOUNT_ID, 0
    )

    assert check_nodes(neo4j_session, "S3Object", ["key"]) == set()


def test_transform_s3_objects_filters_directories():
    """Test transform filters out directory markers (0-byte objects ending with /)."""
    test_objects = [
        {
            "Key": "folder/",
            "Size": 0,
            "LastModified": datetime.datetime(
                2025, 5, 20, 10, 0, 0, tzinfo=timezone.utc
            ),
            "ETag": "d41d8cd98f00b204e9800998ecf8427e",
            "StorageClass": "STANDARD",
        },
        {
            "Key": "folder/file.txt",
            "Size": 100,
            "LastModified": datetime.datetime(
                2025, 5, 20, 10, 0, 0, tzinfo=timezone.utc
            ),
            "ETag": "abc123",
            "StorageClass": "STANDARD",
        },
    ]

    result = transform_s3_objects(
        test_objects, TEST_BUCKET_NAME, TEST_BUCKET_ARN, TEST_REGION, TEST_ACCOUNT_ID
    )

    assert len(result) == 1
    assert result[0]["Key"] == "folder/file.txt"
