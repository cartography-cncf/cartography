# tests/integration/cartography/intel/aws/test_s3object.py
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.s3_objects
import tests.data.aws.s3object
from cartography.intel.aws.s3_objects import sync
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.s3_objects,
    "get_s3_objects_for_bucket",
    return_value=tests.data.aws.s3object.LIST_S3_OBJECTS,
)
def test_sync_s3_objects(mock_get_objects, neo4j_session):
    """
    Test syncing S3 objects.
    """
    boto3_session = MagicMock()
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
        bucket_arn="arn:aws:s3:::test-bucket",
        bucket_name="test-bucket",
        region=TEST_REGION,
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    expected_arns = {
        ("arn:aws:s3:::test-bucket/documents/report.pdf",),
        ("arn:aws:s3:::test-bucket/images/logo.png",),
        ("arn:aws:s3:::test-bucket/archive/old-data.zip",),
    }
    assert check_nodes(neo4j_session, "S3Object", ["arn"]) == expected_arns

    # Verify relationships
    expected_rels = {
        (TEST_ACCOUNT_ID, "arn:aws:s3:::test-bucket/documents/report.pdf"),
        (TEST_ACCOUNT_ID, "arn:aws:s3:::test-bucket/images/logo.png"),
        (TEST_ACCOUNT_ID, "arn:aws:s3:::test-bucket/archive/old-data.zip"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AWSAccount",
            "id",
            "S3Object",
            "arn",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.aws.s3_objects,
    "get_s3_objects_for_bucket",
    return_value=tests.data.aws.s3object.EMPTY_BUCKET_OBJECTS,
)
def test_sync_s3_objects_empty_bucket(mock_get_objects, neo4j_session):
    """
    Test syncing an empty bucket.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    neo4j_session.run("MATCH (n:S3Object) DETACH DELETE n")

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
        bucket_arn="arn:aws:s3:::empty-bucket",
        bucket_name="empty-bucket",
        region=TEST_REGION,
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(neo4j_session, "S3Object", ["arn"]) == set()


@patch.object(
    cartography.intel.aws.s3_objects,
    "get_s3_objects_for_bucket",
    return_value=tests.data.aws.s3object.SINGLE_GLACIER_OBJECT,
)
def test_sync_s3_objects_glacier_restore(mock_get_objects, neo4j_session):
    """
    Test syncing Glacier objects with restore status.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    neo4j_session.run("MATCH (n:S3Object) DETACH DELETE n")

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
        bucket_arn="arn:aws:s3:::test-bucket",
        bucket_name="test-bucket",
        region=TEST_REGION,
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    nodes = neo4j_session.run(
        """
        MATCH (o:S3Object{arn: 'arn:aws:s3:::test-bucket/archive/old-data.zip'})
        RETURN o.storage_class as storage_class,
               o.is_restore_in_progress as is_restore_in_progress,
               o.restore_expiry_date as restore_expiry_date
        """
    )

    result = nodes.single()
    assert result["storage_class"] == "GLACIER"
    assert result["is_restore_in_progress"] is True
    assert result["restore_expiry_date"] is not None


@patch.object(
    cartography.intel.aws.s3_objects,
    "get_s3_objects_for_bucket",
    return_value=tests.data.aws.s3object.SINGLE_OBJECT_WITH_OWNER,
)
def test_sync_s3_objects_with_owner(mock_get_objects, neo4j_session):
    """
    Test syncing S3 objects with owner information.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    neo4j_session.run("MATCH (n:S3Object) DETACH DELETE n")

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
        bucket_arn="arn:aws:s3:::test-bucket",
        bucket_name="test-bucket",
        region=TEST_REGION,
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    nodes = neo4j_session.run(
        """
        MATCH (o:S3Object{arn: 'arn:aws:s3:::test-bucket/images/logo.png'})
        RETURN o.owner_id as owner_id, o.owner_display_name as owner_display_name
        """
    )

    result = nodes.single()
    assert result["owner_id"] == "owner-id-123"
    assert result["owner_display_name"] == "test-owner"


@patch.object(
    cartography.intel.aws.s3_objects,
    "get_s3_objects_for_bucket",
    return_value=tests.data.aws.s3object.EMPTY_BUCKET_OBJECTS,
)
def test_sync_s3_objects_disabled(mock_get_objects, neo4j_session):
    """
    Test that S3 object sync can be disabled.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    neo4j_session.run("MATCH (n:S3Object) DETACH DELETE n")

    # Create a bucket
    neo4j_session.run(
        """
        MERGE (b:S3Bucket{id: 'arn:aws:s3:::test-bucket'})
        SET b.name = 'test-bucket',
            b.region = $region,
            b.lastupdated = $update_tag
        WITH b
        MATCH (a:AWSAccount{id: $account_id})
        MERGE (a)-[r:RESOURCE]->(b)
        SET r.lastupdated = $update_tag
    """,
        region=TEST_REGION,
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Sync with disabled S3 objects
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_ACCOUNT_ID,
            "aws_s3_object_max_per_bucket": 0,  # Disabled
        },
    )

    # Verify the function was called with max_objects=0
    mock_get_objects.assert_called()

    # Check that it was called with the correct parameters
    call_args = mock_get_objects.call_args_list
    for call in call_args:
        # Verify max_objects parameter is 0
        assert call[0][3] == 0  # max_objects is the 4th positional argument

    # Verify no objects were created
    nodes = neo4j_session.run(
        """
        MATCH (n:S3Object) RETURN n.id;
        """
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == set()
