from datetime import datetime
from datetime import timezone

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789

KMS_KEY_ID = "11111111-2222-3333-4444-555555555555"
KMS_KEY_ARN = f"arn:aws:kms:{TEST_REGION}:{TEST_ACCOUNT_ID}:key/{KMS_KEY_ID}"

GET_BACKUP_VAULTS = [
    {
        "BackupVaultName": "Default",
        "BackupVaultArn": (
            f"arn:aws:backup:{TEST_REGION}:{TEST_ACCOUNT_ID}:backup-vault:Default"
        ),
        "CreationDate": datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
        "EncryptionKeyArn": KMS_KEY_ARN,
        "NumberOfRecoveryPoints": 2,
        "Locked": False,
        "MinRetentionDays": 7,
        "MaxRetentionDays": 35,
    },
    {
        "BackupVaultName": "locked-vault",
        "BackupVaultArn": (
            f"arn:aws:backup:{TEST_REGION}:{TEST_ACCOUNT_ID}:backup-vault:locked-vault"
        ),
        "CreationDate": datetime(2024, 6, 1, tzinfo=timezone.utc),
        "NumberOfRecoveryPoints": 0,
        "Locked": True,
        "MinRetentionDays": 30,
        "MaxRetentionDays": 365,
    },
]

PLAN_ID_DAILY = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
PLAN_ID_WEEKLY = "ffffffff-1111-2222-3333-444444444444"

GET_BACKUP_PLANS = [
    {
        "BackupPlanId": PLAN_ID_DAILY,
        "BackupPlanArn": (
            f"arn:aws:backup:{TEST_REGION}:{TEST_ACCOUNT_ID}"
            f":backup-plan:{PLAN_ID_DAILY}"
        ),
        "BackupPlanName": "daily-plan",
        "VersionId": "version-1",
        "CreationDate": datetime(2024, 2, 1, 12, 0, tzinfo=timezone.utc),
        "LastExecutionDate": datetime(2024, 3, 1, 12, 0, tzinfo=timezone.utc),
    },
    {
        "BackupPlanId": PLAN_ID_WEEKLY,
        "BackupPlanArn": (
            f"arn:aws:backup:{TEST_REGION}:{TEST_ACCOUNT_ID}"
            f":backup-plan:{PLAN_ID_WEEKLY}"
        ),
        "BackupPlanName": "weekly-plan",
        "VersionId": "version-2",
        "CreationDate": datetime(2024, 2, 2, 12, 0, tzinfo=timezone.utc),
    },
]
