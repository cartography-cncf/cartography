import copy
from unittest.mock import MagicMock
from unittest.mock import patch

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
    return_value=copy.deepcopy(GET_BACKUP_PLANS),
)
@patch.object(
    cartography.intel.aws.backup,
    "get_backup_vaults",
    return_value=copy.deepcopy(GET_BACKUP_VAULTS),
)
def test_sync_backup(mock_get_vaults, mock_get_plans, neo4j_session):
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

    cartography.intel.aws.backup.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(
        neo4j_session,
        "AWSBackupBackupVault",
        [
            "id",
            "arn",
            "name",
            "encryption_key_arn",
            "number_of_recovery_points",
            "locked",
            "min_retention_days",
            "max_retention_days",
        ],
    ) == {
        (VAULT_DEFAULT_ARN, VAULT_DEFAULT_ARN, "Default", KMS_KEY_ARN, 2, False, 7, 35),
        (VAULT_LOCKED_ARN, VAULT_LOCKED_ARN, "locked-vault", None, 0, True, 30, 365),
    }

    assert check_nodes(
        neo4j_session,
        "AWSBackupBackupPlan",
        ["id", "arn", "name", "version_id"],
    ) == {
        (PLAN_ID_DAILY, PLAN_DAILY_ARN, "daily-plan", "version-1"),
        (PLAN_ID_WEEKLY, PLAN_WEEKLY_ARN, "weekly-plan", "version-2"),
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

    vault_dates = {
        row["name"]: (row["created"], row["region"])
        for row in neo4j_session.run(
            """
            MATCH (n:AWSBackupBackupVault)
            RETURN n.name AS name,
                   n.creation_date IS NOT NULL AS created,
                   n.region AS region
            """,
        )
    }
    assert vault_dates == {
        "Default": (True, TEST_REGION),
        "locked-vault": (True, TEST_REGION),
    }
    plan_dates = {
        row["id"]: (row["created"], row["executed"])
        for row in neo4j_session.run(
            """
            MATCH (n:AWSBackupBackupPlan)
            RETURN n.id AS id,
                   n.creation_date IS NOT NULL AS created,
                   n.last_execution_date IS NOT NULL AS executed
            """,
        )
    }
    assert plan_dates == {
        PLAN_ID_DAILY: (True, True),
        PLAN_ID_WEEKLY: (True, False),
    }


def test_cleanup_backup(neo4j_session):
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    cartography.intel.aws.backup.load_backup_vaults(
        neo4j_session,
        copy.deepcopy(GET_BACKUP_VAULTS[:1]),
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    cartography.intel.aws.backup.load_backup_plans(
        neo4j_session,
        copy.deepcopy(GET_BACKUP_PLANS[:1]),
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    cartography.intel.aws.backup.cleanup(
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(neo4j_session, "AWSBackupBackupVault", ["id"]) == set()
    assert check_nodes(neo4j_session, "AWSBackupBackupPlan", ["id"]) == set()
