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


GRAPH_TOKEN = jwt.encode(
    {
        "aud": "https://graph.microsoft.com",
        "tid": "tenant-id",
        "exp": int(time.time()) + 3600,
    },
    "test-signing-key-not-verified-by-cartography",
    "HS256",
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
        microsoft_access_token=GRAPH_TOKEN,
    )

    entra.start_entra_ingestion(MagicMock(), config)

    for name, sync in syncs.items():
        assert sync.await_args is not None, name
        assert sync.await_args.kwargs == {
            "delegated_auth": True,
            "access_token": GRAPH_TOKEN,
        }, name


def test_entra_ingestion_rejects_arm_token_before_syncing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sync_tenant = AsyncMock()
    monkeypatch.setattr(entra, "sync_tenant", sync_tenant)
    arm_token = jwt.encode(
        {
            "aud": "https://management.azure.com",
            "tid": "tenant-id",
            "exp": int(time.time()) + 3600,
        },
        "test-signing-key-not-verified-by-cartography",
        "HS256",
    )
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=1,
        microsoft_tenant_id="tenant-id",
        microsoft_access_token=arm_token,
    )

    with pytest.raises(ValueError, match="not issued for Microsoft Graph"):
        entra.start_entra_ingestion(MagicMock(), config)
    sync_tenant.assert_not_awaited()
