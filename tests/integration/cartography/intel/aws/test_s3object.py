import copy
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.s3_objects
from cartography.intel.aws.s3_objects import sync
from tests.data.aws.s3_objects import EMPTY_BUCKET_OBJECTS
from tests.data.aws.s3_objects import LIST_S3_OBJECTS
from tests.data.aws.s3_objects import SINGLE_GLACIER_OBJECT
from tests.data.aws.s3_objects import SINGLE_OBJECT_WITH_OWNER
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.s3_objects,
    "get_s3_objects_for_bucket",
    return_value=copy.deepcopy(LIST_S3_OBJECTS),
)
def test_sync_s3_objects(mock_get_objects, neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

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

    neo4j_session.run("MATCH (o:S3Object) DETACH DELETE o")

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
    }

    assert check_rels(
        neo4j_session,
        "S3Object",
        "key",
        "S3Bucket",
        "name",
        "STORED_IN",
        rel_direction_right=True,
    ) == {
        ("documents/report.pdf", "test-bucket"),
        ("images/logo.png", "test-bucket"),
        ("archive/old-data.zip", "test-bucket"),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "S3Object",
        "key",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "documents/report.pdf"),
        (TEST_ACCOUNT_ID, "images/logo.png"),
        (TEST_ACCOUNT_ID, "archive/old-data.zip"),
    }


@patch.object(
    cartography.intel.aws.s3_objects,
    "get_s3_objects_for_bucket",
    return_value=EMPTY_BUCKET_OBJECTS,
)
def test_sync_s3_objects_empty_bucket(mock_get_objects, neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

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
    return_value=copy.deepcopy(SINGLE_OBJECT_WITH_OWNER),
)
def test_sync_s3_objects_with_owner(mock_get_objects, neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

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
        fetch_owner=True,
    )

    assert check_nodes(
        neo4j_session, "S3Object", ["key", "owner_id", "owner_display_name"]
    ) == {("images/logo.png", "owner-id-123", "test-owner")}


@patch.object(
    cartography.intel.aws.s3_objects,
    "get_s3_objects_for_bucket",
    return_value=copy.deepcopy(SINGLE_GLACIER_OBJECT),
)
def test_sync_s3_objects_glacier_restore(mock_get_objects, neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")

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

    assert check_nodes(
        neo4j_session, "S3Object", ["key", "storage_class", "is_restore_in_progress"]
    ) == {("archive/old-data.zip", "GLACIER", True)}
