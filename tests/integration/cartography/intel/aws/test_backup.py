from unittest.mock import MagicMock
from unittest.mock import patch

from botocore.exceptions import ClientError

import cartography.intel.aws.backup
from tests.data.aws.backup import GET_BACKUP_PLANS
from tests.data.aws.backup import GET_BACKUP_VAULTS
from tests.data.aws.backup import KMS_KEY_ARN
from tests.data.aws.backup import KMS_KEY_ID
from tests.data.aws.backup import PLAN_ID_DAILY
from tests.data.aws.backup import PLAN_ID_WEEKLY
from tests.data.aws.backup import TEST_ACCOUNT_ID
from tests.data.aws.backup import TEST_REGION
from tests.data.aws.backup import TEST_UPDATE_TAG
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

VAULT_DEFAULT_ARN = GET_BACKUP_VAULTS[0]["BackupVaultArn"]
VAULT_LOCKED_ARN = GET_BACKUP_VAULTS[1]["BackupVaultArn"]
PLAN_DAILY_ARN = GET_BACKUP_PLANS[0]["BackupPlanArn"]
PLAN_WEEKLY_ARN = GET_BACKUP_PLANS[1]["BackupPlanArn"]


@patch.object(
    cartography.intel.aws.backup,
    "get_backup_plans",
    return_value=GET_BACKUP_PLANS,
)
@patch.object(
    cartography.intel.aws.backup,
    "get_backup_vaults",
    return_value=GET_BACKUP_VAULTS,
)
def test_sync_backup(mock_get_vaults, mock_get_plans, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    neo4j_session.run(
        """
        MERGE (k:AWSKMSKey {id: $key_id})
        SET k.arn = $key_arn, k.lastupdated = $update_tag
        """,
        key_id=KMS_KEY_ID,
        key_arn=KMS_KEY_ARN,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.aws.backup.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "AWSBackupBackupVault",
        [
            "id",
            "arn",
            "name",
            "encryption_key_arn",
            "locked",
            "min_retention_days",
            "max_retention_days",
            "region",
        ],
    ) == {
        (
            VAULT_DEFAULT_ARN,
            VAULT_DEFAULT_ARN,
            "Default",
            KMS_KEY_ARN,
            False,
            7,
            35,
            TEST_REGION,
        ),
        (
            VAULT_LOCKED_ARN,
            VAULT_LOCKED_ARN,
            "locked-vault",
            None,
            True,
            30,
            365,
            TEST_REGION,
        ),
    }

    assert check_nodes(
        neo4j_session,
        "AWSBackupBackupPlan",
        ["id", "arn", "name", "version_id", "region"],
    ) == {
        (PLAN_ID_DAILY, PLAN_DAILY_ARN, "daily-plan", "version-1", TEST_REGION),
        (PLAN_ID_WEEKLY, PLAN_WEEKLY_ARN, "weekly-plan", "version-2", TEST_REGION),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSBackupBackupVault",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, VAULT_DEFAULT_ARN),
        (TEST_ACCOUNT_ID, VAULT_LOCKED_ARN),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSBackupBackupPlan",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, PLAN_DAILY_ARN),
        (TEST_ACCOUNT_ID, PLAN_WEEKLY_ARN),
    }

    assert check_rels(
        neo4j_session,
        "AWSBackupBackupVault",
        "arn",
        "AWSKMSKey",
        "arn",
        "ENCRYPTED_BY",
        rel_direction_right=True,
    ) == {
        (VAULT_DEFAULT_ARN, KMS_KEY_ARN),
    }


def test_sync_backup_keeps_data_when_region_fails(neo4j_session):
    # Arrange
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    with (
        patch.object(
            cartography.intel.aws.backup,
            "get_backup_vaults",
            return_value=GET_BACKUP_VAULTS,
        ),
        patch.object(
            cartography.intel.aws.backup,
            "get_backup_plans",
            return_value=GET_BACKUP_PLANS,
        ),
    ):
        cartography.intel.aws.backup.sync(
            neo4j_session,
            MagicMock(),
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        )

    boto3_session = MagicMock()
    paginator = boto3_session.client.return_value.get_paginator.return_value
    paginator.paginate.side_effect = ClientError(
        {
            "Error": {"Code": "InternalServerErrorException", "Message": ""},
            "ResponseMetadata": {"HTTPStatusCode": 500},
        },
        "ListBackupVaults",
    )

    # Act
    cartography.intel.aws.backup.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSBackupBackupVault", ["id"]) == {
        (VAULT_DEFAULT_ARN,),
        (VAULT_LOCKED_ARN,),
    }
    assert check_nodes(neo4j_session, "AWSBackupBackupPlan", ["id"]) == {
        (PLAN_ID_DAILY,),
        (PLAN_ID_WEEKLY,),
    }
