"""start_entra_ingestion with only a certificate configured: every sub-sync must
receive the certificate path (and password) it needs to build its own
credential. The config and make_credential tests cover the two ends; this
covers the forwarding between them, which is where an argument silently
dropped from one call would otherwise stay green.
"""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.microsoft.entra as entra
from cartography.config import Config

SUB_SYNCS = (
    "sync_entra_users",
    "sync_entra_groups",
    "sync_entra_ous",
    "sync_entra_applications",
    "sync_service_principals",
    "sync_app_role_assignments",
    "sync_entra_directory_roles",
)
ALL_SYNCS = ("sync_tenant", *SUB_SYNCS, "sync_entra_federation")


def _certificate_only_config(password: str | None = None) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=123,
        microsoft_tenant_id="tenant-id",
        microsoft_client_id="client-id",
        microsoft_client_certificate_path="/run/secrets/app.pfx",
        microsoft_client_certificate_password=password,
    )


def test_start_entra_ingestion_forwards_the_certificate_to_every_sync() -> None:
    # Arrange: no secret anywhere, only the certificate and its password
    config = _certificate_only_config(password="pfx-password")
    session = MagicMock()
    mocks = {name: AsyncMock() for name in ALL_SYNCS}

    # Act
    with patch.multiple(entra, **mocks):
        entra.start_entra_ingestion(session, config)

    # Assert: the tenant load and each resource sync ran once, with
    # client_secret=None positionally and the certificate as keywords
    mocks["sync_tenant"].assert_awaited_once_with(
        session,
        "tenant-id",
        "client-id",
        None,
        123,
        client_certificate_path="/run/secrets/app.pfx",
        client_certificate_password="pfx-password",
    )
    common_job_parameters = {"UPDATE_TAG": 123, "TENANT_ID": "tenant-id"}
    for name in SUB_SYNCS:
        mocks[name].assert_awaited_once_with(
            session,
            "tenant-id",
            "client-id",
            None,
            123,
            common_job_parameters,
            client_certificate_path="/run/secrets/app.pfx",
            client_certificate_password="pfx-password",
        )
    mocks["sync_entra_federation"].assert_awaited_once()


def test_start_entra_ingestion_runs_with_a_certificate_and_no_secret() -> None:
    # The module gate used to require a secret; a certificate alone is enough,
    # and an unencrypted file forwards no password.
    config = _certificate_only_config()
    mocks = {name: AsyncMock() for name in ALL_SYNCS}

    with patch.multiple(entra, **mocks):
        entra.start_entra_ingestion(MagicMock(), config)

    assert all(m.await_count == 1 for m in mocks.values())
    users_call = mocks["sync_entra_users"].await_args
    assert users_call is not None
    assert users_call.kwargs["client_certificate_password"] is None


def test_start_entra_ingestion_skips_without_any_credential() -> None:
    config = Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=123,
        microsoft_tenant_id="tenant-id",
        microsoft_client_id="client-id",
    )
    mocks = {name: AsyncMock() for name in ALL_SYNCS}

    with patch.multiple(entra, **mocks):
        entra.start_entra_ingestion(MagicMock(), config)

    assert all(m.await_count == 0 for m in mocks.values())
