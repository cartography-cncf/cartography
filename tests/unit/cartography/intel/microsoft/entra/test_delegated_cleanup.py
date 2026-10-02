import asyncio
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from cartography.intel.microsoft import credentials
from cartography.intel.microsoft.entra import app_role_assignments
from cartography.intel.microsoft.entra import applications
from cartography.intel.microsoft.entra import directory_roles
from cartography.intel.microsoft.entra import groups
from cartography.intel.microsoft.entra import ou
from cartography.intel.microsoft.entra import service_principals
from cartography.intel.microsoft.entra import users


async def _empty_async_iterator(
    *args: object,
    **kwargs: object,
) -> AsyncIterator[None]:
    if False:
        yield None


@pytest.mark.parametrize(  # type: ignore[misc]
    ("module", "getter_name", "cleanup_name", "sync"),
    (
        (users, "get_users", "cleanup", users.sync_entra_users),
        (groups, "get_entra_groups", "cleanup_groups", groups.sync_entra_groups),
        (ou, "get_entra_ous", "cleanup_ous", ou.sync_entra_ous),
        (
            applications,
            "get_entra_applications",
            "cleanup_applications",
            applications.sync_entra_applications,
        ),
        (
            service_principals,
            "get_entra_service_principals",
            "cleanup_service_principals",
            service_principals.sync_service_principals,
        ),
    ),
)
def test_delegated_collection_does_not_cleanup(
    monkeypatch: pytest.MonkeyPatch,
    module,
    getter_name: str,
    cleanup_name: str,
    sync,
) -> None:
    # Arrange
    monkeypatch.setattr(credentials, "make_credential", MagicMock())
    monkeypatch.setattr(module, "GraphServiceClient", MagicMock())
    monkeypatch.setattr(module, getter_name, _empty_async_iterator)
    cleanup = MagicMock()
    monkeypatch.setattr(module, cleanup_name, cleanup)
    analysis = MagicMock()
    if module is service_principals:
        monkeypatch.setattr(module, "run_typed_analysis_job", analysis)

    # Act
    asyncio.run(
        sync(
            MagicMock(),
            "tenant-id",
            None,
            None,
            1234567890,
            {"TENANT_ID": "tenant-id", "UPDATE_TAG": 1234567890},
            delegated_auth=True,
        ),
    )

    # Assert
    cleanup.assert_not_called()
    if module is service_principals:
        analysis.assert_not_called()


def test_application_collection_runs_cleanup(monkeypatch) -> None:
    # Arrange
    monkeypatch.setattr(credentials, "make_credential", MagicMock())
    monkeypatch.setattr(users, "GraphServiceClient", MagicMock())
    monkeypatch.setattr(users, "get_users", _empty_async_iterator)
    cleanup = MagicMock()
    monkeypatch.setattr(users, "cleanup", cleanup)

    # Act
    asyncio.run(
        users.sync_entra_users(
            MagicMock(),
            "tenant-id",
            "client-id",
            "client-secret",
            1234567890,
            {"TENANT_ID": "tenant-id", "UPDATE_TAG": 1234567890},
        ),
    )

    # Assert
    cleanup.assert_called_once()


def test_delegated_app_role_collection_does_not_cleanup(monkeypatch) -> None:
    # Arrange
    monkeypatch.setattr(credentials, "make_credential", MagicMock())
    monkeypatch.setattr(app_role_assignments, "GraphServiceClient", MagicMock())
    cleanup = MagicMock()
    monkeypatch.setattr(
        app_role_assignments,
        "cleanup_app_role_assignments",
        cleanup,
    )
    neo4j_session = MagicMock()
    neo4j_session.execute_read.return_value = []

    # Act
    asyncio.run(
        app_role_assignments.sync_app_role_assignments(
            neo4j_session,
            "tenant-id",
            None,
            None,
            1234567890,
            {"TENANT_ID": "tenant-id", "UPDATE_TAG": 1234567890},
            delegated_auth=True,
        ),
    )

    # Assert
    cleanup.assert_not_called()


def test_delegated_directory_role_collection_does_not_cleanup(monkeypatch) -> None:
    # Arrange
    monkeypatch.setattr(credentials, "make_credential", MagicMock())
    monkeypatch.setattr(directory_roles, "GraphServiceClient", MagicMock())
    monkeypatch.setattr(
        directory_roles, "get_role_definitions", AsyncMock(return_value=[])
    )
    monkeypatch.setattr(
        directory_roles, "get_role_assignments", AsyncMock(return_value=[])
    )
    monkeypatch.setattr(directory_roles, "load_role_definitions", MagicMock())
    monkeypatch.setattr(directory_roles, "load_role_assignments", MagicMock())
    cleanup = MagicMock()
    monkeypatch.setattr(directory_roles, "cleanup_directory_roles", cleanup)

    # Act
    asyncio.run(
        directory_roles.sync_entra_directory_roles(
            MagicMock(),
            "tenant-id",
            None,
            None,
            1234567890,
            {"TENANT_ID": "tenant-id", "UPDATE_TAG": 1234567890},
            delegated_auth=True,
        ),
    )

    # Assert
    cleanup.assert_not_called()
