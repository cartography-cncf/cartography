from unittest.mock import MagicMock

from cartography.intel.aws.backup import get_backup_plans
from cartography.intel.aws.backup import get_backup_vaults
from tests.data.aws.backup import GET_BACKUP_PLANS
from tests.data.aws.backup import GET_BACKUP_VAULTS


def _session_with_pages(pages: list[dict]) -> MagicMock:
    paginator = MagicMock()
    paginator.paginate.return_value = pages
    client = MagicMock()
    client.get_paginator.return_value = paginator
    session = MagicMock()
    session.client.return_value = client
    return session


def test_get_backup_vaults_paginates() -> None:
    session = _session_with_pages(
        [
            {"BackupVaultList": GET_BACKUP_VAULTS[:1]},
            {"BackupVaultList": GET_BACKUP_VAULTS[1:]},
        ],
    )

    assert get_backup_vaults(session, "us-east-1") == GET_BACKUP_VAULTS
    session.client.return_value.get_paginator.assert_called_once_with(
        "list_backup_vaults",
    )


def test_get_backup_plans_paginates() -> None:
    session = _session_with_pages(
        [
            {"BackupPlansList": GET_BACKUP_PLANS[:1]},
            {"BackupPlansList": GET_BACKUP_PLANS[1:]},
        ],
    )

    assert get_backup_plans(session, "us-east-1") == GET_BACKUP_PLANS
    session.client.return_value.get_paginator.assert_called_once_with(
        "list_backup_plans",
    )
