from unittest.mock import AsyncMock
from unittest.mock import MagicMock

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


def test_entra_ingestion_passes_access_token_to_every_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    syncs = {name: AsyncMock() for name in ENTRA_SYNCS}
    for name, sync in syncs.items():
        monkeypatch.setattr(entra, name, sync)
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=1,
        microsoft_tenant_id="tenant-id",
        microsoft_access_token="graph-token",
    )

    entra.start_entra_ingestion(MagicMock(), config)

    for name, sync in syncs.items():
        assert sync.await_args is not None, name
        assert sync.await_args.kwargs == {
            "delegated_auth": True,
            "access_token": "graph-token",
        }, name
