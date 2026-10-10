import time
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import jwt
import pytest

import cartography.intel.microsoft.entra as entra
from cartography.config import Config

ENTRA_SYNCS = (
    "sync_tenant",
    "sync_entra_users",
    "sync_entra_groups",
    "sync_entra_ous",
    "sync_entra_applications",
    "sync_service_principals",
    "sync_app_role_assignments",
    "sync_entra_directory_roles",
)


def _token(audience: str) -> str:
    return jwt.encode(
        {"aud": audience, "tid": "tenant-id", "exp": int(time.time()) + 3600},
        "test-signing-key-not-verified-by-cartography",
        "HS256",
    )


def _config(access_token: str) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=1,
        microsoft_tenant_id="tenant-id",
        microsoft_access_token=access_token,
    )


def test_entra_ingestion_passes_access_token_to_every_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    syncs = {name: AsyncMock() for name in ENTRA_SYNCS}
    for name, sync in syncs.items():
        monkeypatch.setattr(entra, name, sync)
    token = _token("https://graph.microsoft.com")

    # Act
    entra.start_entra_ingestion(MagicMock(), _config(token))

    # Assert
    for name, sync in syncs.items():
        assert sync.await_args is not None, name
        assert sync.await_args.kwargs == {
            "delegated_auth": True,
            "access_token": token,
        }, name


def test_entra_ingestion_rejects_arm_token_before_syncing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    sync_tenant = AsyncMock()
    monkeypatch.setattr(entra, "sync_tenant", sync_tenant)
    config = _config(_token("https://management.azure.com"))

    # Act
    with pytest.raises(ValueError, match="not issued for Microsoft Graph"):
        entra.start_entra_ingestion(MagicMock(), config)

    # Assert
    sync_tenant.assert_not_awaited()
