from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j.time

import cartography.intel.aws.dynamodb
import tests.data.aws.dynamodb
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.dynamodb,
    "get_dynamodb_tables",
    return_value=tests.data.aws.dynamodb.LIST_DYNAMODB_TABLES["Tables"],
)
def test_load_dynamodb(mock_get_instances, neo4j_session):
    """
    Ensure that instances actually get loaded and have their key fields
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.aws.dynamodb.sync_dynamodb_tables(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert ddb table nodes exist
    assert check_nodes(
        neo4j_session,
        "DynamoDBTable",
        [
            "id",
            "rows",
            "archival_backup_arn",
            "archival_date_time",
            "archival_reason",
            "billing_mode",
            "creation_date_time",
            "last_update_to_pay_per_request_date_time",
            "latest_stream_arn",
            "latest_stream_label",
            "restore_date_time",
            "restore_in_progress",
            "source_backup_arn",
            "source_table_arn",
            "sse_status",
            "sse_type",
            "sse_kms_key_arn",
            "stream_enabled",
            "stream_view_type",
            "table_status",
        ],
    ) == {
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/example-table",
            1000000,
            None,
            None,
            None,
            "PROVISIONED",
            neo4j.time.DateTime(2019, 1, 1, 0, 0, 1),
            neo4j.time.DateTime(2020, 6, 15, 10, 30, 0),
            "arn:aws:dynamodb:us-east-1:table/example-table/stream/0000-00-00000:00:00.000",
            "0000-00-00000:00:00.000",
            None,
            None,
            None,
            None,
            "ENABLED",
            "KMS",
            "arn:aws:kms:us-east-1:000000000000:key/12345678-1234-1234-1234-123456789012",
            True,
            "SAMPLE_STREAM_VIEW_TYPE",
            "ACTIVE",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/sample-table",
            1000000,
            None,
            None,
            None,
            "PAY_PER_REQUEST",
            neo4j.time.DateTime(2019, 1, 1, 0, 0, 1),
            None,
            "arn:aws:dynamodb:us-east-1:table/sample-table/stream/0000-00-00000:00:00.000",
            "0000-00-00000:00:00.000",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "ACTIVE",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/model-table",
            1000000,
            None,
            None,
            None,
            None,
            neo4j.time.DateTime(2019, 1, 1, 0, 0, 1),
            None,
            "arn:aws:dynamodb:us-east-1:table/model-table/stream/0000-00-00000:00:00.000",
            "0000-00-00000:00:00.000",
            neo4j.time.DateTime(2021, 3, 10, 14, 25, 0),
            False,
            "arn:aws:dynamodb:us-east-1:000000000000:table/model-table/backup/01234567890123-abcdefgh",
            "arn:aws:dynamodb:us-east-1:000000000000:table/original-model-table",
            None,
            None,
            None,
            True,
            "NEW_AND_OLD_IMAGES",
            "ACTIVE",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/basic-table",
            1000000,
            None,
            None,
            None,
            None,
            neo4j.time.DateTime(2019, 1, 1, 0, 0, 1),
            None,
            "arn:aws:dynamodb:us-east-1:table/basic-table/stream/0000-00-00000:00:00.000",
            "0000-00-00000:00:00.000",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "ACTIVE",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/archived-table",
            500000,
            "arn:aws:dynamodb:us-east-1:000000000000:table/archived-table/backup/archived-backup-123",
            neo4j.time.DateTime(2022, 8, 20, 9, 15, 0),
            "Manual archival by administrator",
            "PROVISIONED",
            neo4j.time.DateTime(2018, 1, 1, 0, 0, 1),
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "ARCHIVED",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/encrypted-table",
            750000,
            None,
            None,
            None,
            "PROVISIONED",
            neo4j.time.DateTime(2020, 10, 1, 0, 0, 1),
            neo4j.time.DateTime(2021, 2, 10, 16, 45, 30),
            "arn:aws:dynamodb:us-east-1:table/encrypted-table/stream/2021-02-10T16:45:30.000",
            "2021-02-10T16:45:30.000",
            None,
            None,
            None,
            None,
            "ENABLED",
            "KMS",
            "arn:aws:kms:us-east-1:000000000000:key/87654321-4321-4321-4321-210987654321",
            True,
            "KEYS_ONLY",
            "ACTIVE",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/restored-table",
            600000,
            None,
            None,
            None,
            "PAY_PER_REQUEST",
            neo4j.time.DateTime(2021, 5, 1, 0, 0, 1),
            None,
            None,
            None,
            neo4j.time.DateTime(2021, 5, 15, 10, 30, 0),
            True,
            "arn:aws:dynamodb:us-east-1:000000000000:table/source-table/backup/backup-456",
            "arn:aws:dynamodb:us-east-1:000000000000:table/source-table",
            "ENABLED",
            "AES256",
            None,
            None,
            None,
            "ACTIVE",
        ),
    }

    # Assert ddb gsi nodes exist
    assert check_nodes(neo4j_session, "DynamoDBGlobalSecondaryIndex", ["id"]) == {
        ("arn:aws:dynamodb:us-east-1:table/example-table/index/sample_2-index",),
        ("arn:aws:dynamodb:us-east-1:table/model-table/index/sample_2-index",),
        ("arn:aws:dynamodb:us-east-1:table/model-table/index/sample_3-index",),
        ("arn:aws:dynamodb:us-east-1:table/model-table/index/sample_1-index",),
        ("arn:aws:dynamodb:us-east-1:table/example-table/index/sample_1-index",),
        ("arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_2-index",),
        ("arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_1-index",),
        ("arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_3-index",),
    }

    # Assert AWSAccount -> DynamoDBTable
    assert check_rels(
        neo4j_session,
        "DynamoDBTable",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("arn:aws:dynamodb:us-east-1:000000000000:table/example-table", "000000000000"),
        ("arn:aws:dynamodb:us-east-1:000000000000:table/sample-table", "000000000000"),
        ("arn:aws:dynamodb:us-east-1:000000000000:table/model-table", "000000000000"),
        ("arn:aws:dynamodb:us-east-1:000000000000:table/basic-table", "000000000000"),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/archived-table",
            "000000000000",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/encrypted-table",
            "000000000000",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/restored-table",
            "000000000000",
        ),
    }

    # Assert AWSAccount -> DynamoDBGlobalSecondaryIndex
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "DynamoDBGlobalSecondaryIndex",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            "000000000000",
            "arn:aws:dynamodb:us-east-1:table/example-table/index/sample_1-index",
        ),
        (
            "000000000000",
            "arn:aws:dynamodb:us-east-1:table/example-table/index/sample_2-index",
        ),
        (
            "000000000000",
            "arn:aws:dynamodb:us-east-1:table/model-table/index/sample_1-index",
        ),
        (
            "000000000000",
            "arn:aws:dynamodb:us-east-1:table/model-table/index/sample_2-index",
        ),
        (
            "000000000000",
            "arn:aws:dynamodb:us-east-1:table/model-table/index/sample_3-index",
        ),
        (
            "000000000000",
            "arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_1-index",
        ),
        (
            "000000000000",
            "arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_2-index",
        ),
        (
            "000000000000",
            "arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_3-index",
        ),
    }

    # Assert DynamoDBTable -> DynamoDBGlobalSecondaryIndex
    assert check_rels(
        neo4j_session,
        "DynamoDBTable",
        "id",
        "DynamoDBGlobalSecondaryIndex",
        "id",
        "GLOBAL_SECONDARY_INDEX",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/example-table",
            "arn:aws:dynamodb:us-east-1:table/example-table/index/sample_1-index",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/example-table",
            "arn:aws:dynamodb:us-east-1:table/example-table/index/sample_2-index",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/model-table",
            "arn:aws:dynamodb:us-east-1:table/model-table/index/sample_1-index",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/model-table",
            "arn:aws:dynamodb:us-east-1:table/model-table/index/sample_2-index",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/model-table",
            "arn:aws:dynamodb:us-east-1:table/model-table/index/sample_3-index",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/sample-table",
            "arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_1-index",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/sample-table",
            "arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_2-index",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/sample-table",
            "arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_3-index",
        ),
    }

    # Arrange: load in an unrelated EC2 instance. This should not be affected by the DynamoDB module's cleanup job.
    neo4j_session.run(
        """
        MERGE (i:EC2Instance{id:1234, lastupdated: $lastupdated})<-[r:RESOURCE]-(:AWSAccount{id: $aws_account_id})
        SET r.lastupdated = $lastupdated
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        lastupdated=TEST_UPDATE_TAG,
    )

    # [Pre-test] Assert that the unrelated EC2 instance exists
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "EC2Instance",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, 1234),
    }

    # Act: run the cleanup job
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG
        + 1,  # Simulate a new sync run finished so the old update tag is obsolete now
        "AWS_ID": TEST_ACCOUNT_ID,
        # Add in extra params that may have been added by other modules.
        # Expectation: These should not affect cleanup job execution.
        "permission_relationships_file": "/path/to/perm/rels/file",
        "OKTA_ORG_ID": "my-org-id",
    }
    cartography.intel.aws.dynamodb.cleanup_dynamodb_tables(
        neo4j_session,
        common_job_parameters,
    )

    # Assert: Expect no ddb nodes in the graph now
    assert check_nodes(neo4j_session, "DynamoDBTable", ["id"]) == set()
    assert check_nodes(neo4j_session, "DynamoDBGlobalSecondaryIndex", ["id"]) == set()
    # Assert: Expect that the unrelated EC2 instance was not touched by the cleanup job
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "EC2Instance",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, 1234),
    }


@patch.object(
    cartography.intel.aws.dynamodb,
    "get_dynamodb_tables",
    return_value=tests.data.aws.dynamodb.LIST_DYNAMODB_TABLES["Tables"],
)
def test_load_dynamodb_table_properties(mock_get_instances, neo4j_session):
    """
    Test that new DynamoDB table properties are loaded correctly
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.aws.dynamodb.sync_dynamodb_tables(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert: Check that table with streams has stream properties set
    result = neo4j_session.run(
        """
        MATCH (t:DynamoDBTable{id: $table_arn})
        RETURN t.stream_enabled as stream_enabled,
               t.stream_view_type as stream_view_type,
               t.latest_stream_arn as latest_stream_arn,
               t.latest_stream_label as latest_stream_label,
               t.table_status as table_status,
               t.creation_date_time as creation_date_time
        """,
        table_arn="arn:aws:dynamodb:us-east-1:000000000000:table/example-table",
    ).single()

    assert result["stream_enabled"] is True
    assert result["stream_view_type"] == "SAMPLE_STREAM_VIEW_TYPE"
    assert (
        result["latest_stream_arn"]
        == "arn:aws:dynamodb:us-east-1:table/example-table/stream/0000-00-00000:00:00.000"
    )
    assert result["latest_stream_label"] == "0000-00-00000:00:00.000"
    assert result["table_status"] == "ACTIVE"
    assert result["creation_date_time"] is not None

    # Assert: Check that table without streams still loads correctly
    result = neo4j_session.run(
        """
        MATCH (t:DynamoDBTable{id: $table_arn})
        RETURN t.stream_enabled as stream_enabled,
               t.stream_view_type as stream_view_type,
               t.table_status as table_status
        """,
        table_arn="arn:aws:dynamodb:us-east-1:000000000000:table/sample-table",
    ).single()

    assert result["stream_enabled"] is None
    assert result["stream_view_type"] is None
    assert result["table_status"] == "ACTIVE"


@patch.object(
    cartography.intel.aws.dynamodb,
    "get_dynamodb_tables",
    return_value=tests.data.aws.dynamodb.LIST_DYNAMODB_TABLES["Tables"],
)
def test_load_dynamodb_encryption_properties(mock_get_instances, neo4j_session):
    """
    Test that encryption properties can be loaded (using None values for test data that doesn't have them)
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.aws.dynamodb.sync_dynamodb_tables(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert: Check that encryption properties are present and correct
    result = neo4j_session.run(
        """
        MATCH (t:DynamoDBTable{id: $table_arn})
        RETURN t.sse_status as sse_status,
               t.sse_type as sse_type,
               t.sse_kms_key_arn as sse_kms_key_arn
        """,
        table_arn="arn:aws:dynamodb:us-east-1:000000000000:table/example-table",
    ).single()

    assert result["sse_status"] == "ENABLED"
    assert result["sse_type"] == "KMS"
    assert (
        result["sse_kms_key_arn"]
        == "arn:aws:kms:us-east-1:000000000000:key/12345678-1234-1234-1234-123456789012"
    )
