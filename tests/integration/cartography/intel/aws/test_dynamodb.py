from unittest.mock import MagicMock
from unittest.mock import patch

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
def test_sync_dynamodb_nodes_and_relationships(mock_get_tables, neo4j_session):
    """
    Consolidated test to verify that DynamoDB tables and all related child entities
    (GSIs, Billing, Streams, SSE, Archival, Restore, Backups) are correctly loaded
    and connected in a single sync operation.
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

    # Assert: DynamoDBTable nodes
    assert check_nodes(
        neo4j_session,
        "DynamoDBTable",
        ["id", "rows", "size", "table_status"],
    ) == {
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/example-table",
            1000000,
            100000000,
            "ACTIVE",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/sample-table",
            1000000,
            100000000,
            "ACTIVE",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/model-table",
            1000000,
            100000000,
            "ACTIVE",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/basic-table",
            1000000,
            100000000,
            "ACTIVE",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/archived-table",
            500000,
            50000000,
            "ARCHIVED",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/encrypted-table",
            750000,
            75000000,
            "ACTIVE",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/restored-table",
            600000,
            60000000,
            "ACTIVE",
        ),
    }

    # Assert: GSIs
    assert check_nodes(neo4j_session, "DynamoDBGlobalSecondaryIndex", ["id"]) == {
        ("arn:aws:dynamodb:us-east-1:table/example-table/index/sample_1-index",),
        ("arn:aws:dynamodb:us-east-1:table/example-table/index/sample_2-index",),
        ("arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_1-index",),
        ("arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_2-index",),
        ("arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_3-index",),
        ("arn:aws:dynamodb:us-east-1:table/model-table/index/sample_1-index",),
        ("arn:aws:dynamodb:us-east-1:table/model-table/index/sample_2-index",),
        ("arn:aws:dynamodb:us-east-1:table/model-table/index/sample_3-index",),
    }

    # Assert: Billing entities
    billing_nodes = check_nodes(
        neo4j_session, "DynamoDBBillingModeSummary", ["id", "billing_mode"]
    )
    assert billing_nodes == {
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/example-table/billing",
            "PROVISIONED",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/sample-table/billing",
            "PAY_PER_REQUEST",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/archived-table/billing",
            "PROVISIONED",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/encrypted-table/billing",
            "PROVISIONED",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/restored-table/billing",
            "PAY_PER_REQUEST",
        ),
    }

    # Assert: Stream entities
    stream_nodes = check_nodes(
        neo4j_session, "DynamoDBStream", ["id", "stream_enabled", "stream_view_type"]
    )
    assert stream_nodes == {
        (
            "arn:aws:dynamodb:us-east-1:table/example-table/stream/0000-00-00000:00:00.000",
            True,
            "SAMPLE_STREAM_VIEW_TYPE",
        ),
        (
            "arn:aws:dynamodb:us-east-1:table/model-table/stream/0000-00-00000:00:00.000",
            True,
            "NEW_AND_OLD_IMAGES",
        ),
        (
            "arn:aws:dynamodb:us-east-1:table/encrypted-table/stream/2021-02-10T16:45:30.000",
            True,
            "KEYS_ONLY",
        ),
    }

    # Assert: SSE entities
    sse_nodes = check_nodes(
        neo4j_session,
        "DynamoDBSSEDescription",
        ["id", "sse_status", "sse_type", "kms_master_key_arn"],
    )
    assert sse_nodes == {
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/example-table/sse",
            "ENABLED",
            "KMS",
            "arn:aws:kms:us-east-1:000000000000:key/12345678-1234-1234-1234-123456789012",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/encrypted-table/sse",
            "ENABLED",
            "KMS",
            "arn:aws:kms:us-east-1:000000000000:key/87654321-4321-4321-4321-210987654321",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/restored-table/sse",
            "ENABLED",
            "AES256",
            None,
        ),
    }

    # Assert: Archival entities
    archival_nodes = check_nodes(
        neo4j_session, "DynamoDBArchivalSummary", ["id", "archival_reason"]
    )
    assert archival_nodes == {
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/archived-table/archival",
            "Manual archival by administrator",
        ),
    }

    # Assert: Restore entities
    restore_nodes = check_nodes(
        neo4j_session, "DynamoDBRestoreSummary", ["id", "restore_in_progress"]
    )
    assert restore_nodes == {
        ("arn:aws:dynamodb:us-east-1:000000000000:table/model-table/restore", False),
        ("arn:aws:dynamodb:us-east-1:000000000000:table/restored-table/restore", True),
    }

    # Assert: Backup stubs
    backup_nodes = check_nodes(neo4j_session, "DynamoDBBackup", ["id"])
    assert backup_nodes == {
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/archived-table/backup/archived-backup-123",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/model-table/backup/01234567890123-abcdefgh",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/source-table/backup/backup-456",
        ),
    }

    # Assert: AWSAccount -> DynamoDBTable
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

    # Assert: Billing relationships
    billing_rels = check_rels(
        neo4j_session,
        "DynamoDBTable",
        "id",
        "DynamoDBBillingModeSummary",
        "id",
        "HAS_BILLING",
        rel_direction_right=True,
    )
    assert billing_rels == {
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/example-table",
            "arn:aws:dynamodb:us-east-1:000000000000:table/example-table/billing",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/sample-table",
            "arn:aws:dynamodb:us-east-1:000000000000:table/sample-table/billing",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/archived-table",
            "arn:aws:dynamodb:us-east-1:000000000000:table/archived-table/billing",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/encrypted-table",
            "arn:aws:dynamodb:us-east-1:000000000000:table/encrypted-table/billing",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/restored-table",
            "arn:aws:dynamodb:us-east-1:000000000000:table/restored-table/billing",
        ),
    }

    # Assert: Stream relationships
    stream_rels = check_rels(
        neo4j_session,
        "DynamoDBTable",
        "id",
        "DynamoDBStream",
        "id",
        "LATEST_STREAM",
        rel_direction_right=True,
    )
    assert stream_rels == {
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/example-table",
            "arn:aws:dynamodb:us-east-1:table/example-table/stream/0000-00-00000:00:00.000",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/model-table",
            "arn:aws:dynamodb:us-east-1:table/model-table/stream/0000-00-00000:00:00.000",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/encrypted-table",
            "arn:aws:dynamodb:us-east-1:table/encrypted-table/stream/2021-02-10T16:45:30.000",
        ),
    }

    # Assert: SSE relationships
    sse_rels = check_rels(
        neo4j_session,
        "DynamoDBTable",
        "id",
        "DynamoDBSSEDescription",
        "id",
        "HAS_SSE",
        rel_direction_right=True,
    )
    assert sse_rels == {
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/example-table",
            "arn:aws:dynamodb:us-east-1:000000000000:table/example-table/sse",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/encrypted-table",
            "arn:aws:dynamodb:us-east-1:000000000000:table/encrypted-table/sse",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/restored-table",
            "arn:aws:dynamodb:us-east-1:000000000000:table/restored-table/sse",
        ),
    }

    # Assert: Archival relationships
    archival_rels = check_rels(
        neo4j_session,
        "DynamoDBTable",
        "id",
        "DynamoDBArchivalSummary",
        "id",
        "HAS_ARCHIVAL",
        rel_direction_right=True,
    )
    assert archival_rels == {
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/archived-table",
            "arn:aws:dynamodb:us-east-1:000000000000:table/archived-table/archival",
        ),
    }

    # Assert: Restore relationships
    restore_rels = check_rels(
        neo4j_session,
        "DynamoDBTable",
        "id",
        "DynamoDBRestoreSummary",
        "id",
        "HAS_RESTORE",
        rel_direction_right=True,
    )
    assert restore_rels == {
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/model-table",
            "arn:aws:dynamodb:us-east-1:000000000000:table/model-table/restore",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/restored-table",
            "arn:aws:dynamodb:us-east-1:000000000000:table/restored-table/restore",
        ),
    }

    # Archival -> Backup
    archival_backup_rels = check_rels(
        neo4j_session,
        "DynamoDBArchivalSummary",
        "id",
        "DynamoDBBackup",
        "id",
        "ARCHIVED_TO_BACKUP",
        rel_direction_right=True,
    )
    assert archival_backup_rels == {
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/archived-table/archival",
            "arn:aws:dynamodb:us-east-1:000000000000:table/archived-table/backup/archived-backup-123",
        ),
    }

    # Restore -> Backup
    restore_backup_rels = check_rels(
        neo4j_session,
        "DynamoDBRestoreSummary",
        "id",
        "DynamoDBBackup",
        "id",
        "RESTORED_FROM_BACKUP",
        rel_direction_right=True,
    )
    assert restore_backup_rels == {
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/model-table/restore",
            "arn:aws:dynamodb:us-east-1:000000000000:table/model-table/backup/01234567890123-abcdefgh",
        ),
        (
            "arn:aws:dynamodb:us-east-1:000000000000:table/restored-table/restore",
            "arn:aws:dynamodb:us-east-1:000000000000:table/source-table/backup/backup-456",
        ),
    }

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

    # Act: Run cleanup with a NEW update tag (simulating a subsequent sync where these resources are gone)
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG + 1,
        "AWS_ID": TEST_ACCOUNT_ID,
        # Add in extra params that may have been added by other modules.
        # Expectation: These should not affect cleanup job execution.
        "permission_relationships_file": "/path/to/perm/rels/file",
        "OKTA_ORG_ID": "my-org-id",
    }
    cartography.intel.aws.dynamodb.cleanup_dynamodb(
        neo4j_session,
        common_job_parameters,
    )

    # Assert: All DynamoDB nodes should be cleaned up (because they have the OLD update tag)
    assert check_nodes(neo4j_session, "DynamoDBTable", ["id"]) == set()
    assert check_nodes(neo4j_session, "DynamoDBGlobalSecondaryIndex", ["id"]) == set()
    assert check_nodes(neo4j_session, "DynamoDBBillingModeSummary", ["id"]) == set()
    assert check_nodes(neo4j_session, "DynamoDBStream", ["id"]) == set()
    assert check_nodes(neo4j_session, "DynamoDBSSEDescription", ["id"]) == set()
    assert check_nodes(neo4j_session, "DynamoDBArchivalSummary", ["id"]) == set()
    assert check_nodes(neo4j_session, "DynamoDBRestoreSummary", ["id"]) == set()
    assert check_nodes(neo4j_session, "DynamoDBBackup", ["id"]) == set()

    # Assert: The unrelated EC2 instance should STILL EXIST
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "EC2Instance",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {(TEST_ACCOUNT_ID, 1234)}
