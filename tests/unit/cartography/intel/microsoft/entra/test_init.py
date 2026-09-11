import logging
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from kiota_abstractions.api_error import APIError

from cartography.config import Config
from cartography.intel.microsoft import entra


def test_delegated_auth_continues_after_denied_dataset(monkeypatch, caplog) -> None:
    # Arrange
    sync_names = (
        "sync_tenant",
        "sync_entra_users",
        "sync_entra_groups",
        "sync_entra_ous",
        "sync_entra_applications",
        "sync_service_principals",
        "sync_app_role_assignments",
        "sync_entra_directory_roles",
    )
    syncs = {name: AsyncMock() for name in sync_names}
    denied = APIError("forbidden")
    denied.response_status_code = 403
    syncs["sync_entra_users"].side_effect = denied
    for name, sync in syncs.items():
        monkeypatch.setattr(entra, name, sync)
    federation = AsyncMock()
    monkeypatch.setattr(entra, "sync_entra_federation", federation)
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        microsoft_tenant_id="tenant-id",
        microsoft_delegated_auth=True,
        update_tag=1234567890,
    )

    # Act
    with caplog.at_level(logging.WARNING):
        entra.start_entra_ingestion(MagicMock(), config)

    # Assert
    for sync in syncs.values():
        sync.assert_awaited_once()
        assert sync.call_args.kwargs["delegated_auth"] is True
    federation.assert_not_awaited()
    assert "Skipping Entra users sync" in caplog.text
    assert "Datasets denied by Microsoft Graph: users" in caplog.text


def test_application_auth_still_fails_on_denied_required_dataset(
    monkeypatch,
) -> None:
    # Arrange
    denied = APIError("forbidden")
    denied.response_status_code = 403
    sync_users = AsyncMock(side_effect=denied)
    monkeypatch.setattr(entra, "sync_tenant", AsyncMock())
    monkeypatch.setattr(entra, "sync_entra_users", sync_users)
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        microsoft_tenant_id="tenant-id",
        microsoft_client_id="client-id",
        microsoft_client_secret="client-secret",
        update_tag=1234567890,
    )

    # Act and assert
    with pytest.raises(APIError) as error:
        entra.start_entra_ingestion(MagicMock(), config)
    assert error.value is denied


def test_delegated_auth_does_not_hide_authentication_failures(monkeypatch) -> None:
    # Arrange
    unauthorized = APIError("unauthorized")
    unauthorized.response_status_code = 401
    sync_tenant = AsyncMock(side_effect=unauthorized)
    sync_users = AsyncMock()
    monkeypatch.setattr(entra, "sync_tenant", sync_tenant)
    monkeypatch.setattr(entra, "sync_entra_users", sync_users)
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        microsoft_tenant_id="tenant-id",
        microsoft_delegated_auth=True,
        update_tag=1234567890,
    )

    # Act and assert
    with pytest.raises(APIError) as error:
        entra.start_entra_ingestion(MagicMock(), config)
    assert error.value is unauthorized
    sync_users.assert_not_awaited()
