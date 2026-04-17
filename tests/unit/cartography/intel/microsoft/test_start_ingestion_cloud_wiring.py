"""Verify that ``config.entra_cloud`` flows end-to-end from the ingestion
entry points (``start_entra_ingestion`` / ``start_intune_ingestion``) down
to every ``sync_*`` call and ultimately to ``build_graph_client``.

Regression guard: if a future change adds a new Entra/Intune sync step
without threading the cloud parameter, these tests fail.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.microsoft.entra as entra_pkg
import cartography.intel.microsoft.intune as intune_pkg
from cartography.config import Config
from cartography.intel.microsoft.clouds import COMMERCIAL
from cartography.intel.microsoft.clouds import USGOV

ENTRA_SYNC_FUNCS = [
    "sync_tenant",
    "sync_entra_users",
    "sync_entra_groups",
    "sync_entra_ous",
    "sync_entra_applications",
    "sync_service_principals",
    "sync_app_role_assignments",
]


def _make_config(cloud_name: str | None) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=1,
        entra_tenant_id="tid",
        entra_client_id="cid",
        entra_client_secret="sec",
        entra_cloud=cloud_name,
    )


@pytest.mark.parametrize(
    "cloud_name,expected",
    [(None, COMMERCIAL), ("commercial", COMMERCIAL), ("usgov", USGOV)],
)
def test_start_entra_ingestion_threads_cloud(cloud_name, expected):
    """Every Entra sync_* is called with the resolved cloud."""
    config = _make_config(cloud_name)

    async def _noop(*_args, **_kwargs):
        return None

    with (
        patch.object(entra_pkg, "sync_tenant", side_effect=_noop) as m_tenant,
        patch.object(entra_pkg, "sync_entra_users", side_effect=_noop) as m_users,
        patch.object(entra_pkg, "sync_entra_groups", side_effect=_noop) as m_groups,
        patch.object(entra_pkg, "sync_entra_ous", side_effect=_noop) as m_ous,
        patch.object(entra_pkg, "sync_entra_applications", side_effect=_noop) as m_apps,
        patch.object(entra_pkg, "sync_service_principals", side_effect=_noop) as m_sp,
        patch.object(
            entra_pkg, "sync_app_role_assignments", side_effect=_noop
        ) as m_ara,
        patch.object(entra_pkg, "sync_entra_federation", side_effect=_noop),
    ):
        entra_pkg.start_entra_ingestion(MagicMock(), config)

    for mock in (m_tenant, m_users, m_groups, m_ous, m_apps, m_sp, m_ara):
        assert mock.call_args is not None, f"{mock} was not called"
        assert (
            mock.call_args.args[-1] is expected
        ), f"{mock} got cloud={mock.call_args.args[-1]!r}, expected {expected!r}"


@pytest.mark.parametrize(
    "cloud_name,expected_base_url",
    [
        (None, COMMERCIAL.graph_base_url),
        ("commercial", COMMERCIAL.graph_base_url),
        ("usgov", USGOV.graph_base_url),
    ],
)
def test_start_intune_ingestion_builds_client_for_cloud(cloud_name, expected_base_url):
    """The Graph client constructed by the Intune entry point must use
    the base_url for the cloud named in ``config.entra_cloud``.
    """
    config = _make_config(cloud_name)

    async def _noop(*_args, **_kwargs):
        return None

    with (
        patch.object(intune_pkg, "sync_managed_devices", side_effect=_noop) as m_md,
        patch.object(intune_pkg, "sync_detected_apps", side_effect=_noop),
        patch.object(intune_pkg, "sync_compliance_policies", side_effect=_noop),
        patch.object(intune_pkg, "run_scoped_analysis_job"),
    ):
        intune_pkg.start_intune_ingestion(MagicMock(), config)

    built_client = m_md.call_args.args[1]
    assert built_client.request_adapter.base_url == expected_base_url


def test_start_entra_ingestion_skips_when_unconfigured():
    """Zero-change guarantee: missing credentials still short-circuits."""
    config = Config(neo4j_uri="bolt://localhost:7687", update_tag=1)

    with patch.object(entra_pkg, "sync_tenant") as m_tenant:
        entra_pkg.start_entra_ingestion(MagicMock(), config)

    m_tenant.assert_not_called()
