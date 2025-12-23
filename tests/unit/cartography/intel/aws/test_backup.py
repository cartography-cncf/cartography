from datetime import datetime
from datetime import timezone

from cartography.intel.aws.backup import transform_backup_plans
from cartography.intel.aws.backup import transform_backup_vaults


def test_transform_backup_vaults():
    # Arrange
    raw_vaults = [
        {
            "BackupVaultName": "test-vault",
            "BackupVaultArn": "arn:aws:backup:us-east-1:123456789012:backup-vault:test-vault",
            "CreationDate": datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "LockDate": datetime(2023, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        }
    ]

    # Act
    transformed_vaults = transform_backup_vaults(raw_vaults)

    # Assert
    assert len(transformed_vaults) == 1
    assert transformed_vaults[0]["CreationDate"] == 1672574400
    assert transformed_vaults[0]["LockDate"] == 1685620800


def test_transform_backup_plans():
    # Arrange
    raw_plans = [
        {
            "BackupPlanName": "test-plan",
            "BackupPlanArn": "arn:aws:backup:us-east-1:123456789012:backup-plan:test-plan",
            "CreationDate": datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "DeletionDate": None,
            "LastExecutionDate": datetime(2023, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
        }
    ]

    # Act
    transformed_plans = transform_backup_plans(raw_plans)

    # Assert
    assert len(transformed_plans) == 1
    assert transformed_plans[0]["CreationDate"] == 1672574400
    assert transformed_plans[0]["DeletionDate"] is None
    assert transformed_plans[0]["LastExecutionDate"] == 1672660800
