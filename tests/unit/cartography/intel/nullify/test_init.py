from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.config import Config
from cartography.intel.nullify import start_nullify_ingestion
from cartography.intel.nullify.util import NullifyEnvelopeError


def _config(**overrides):
    base = {
        "neo4j_uri": "bolt://localhost:7687",
        "update_tag": 1,
        "nullify_tenant": "acme",
        "nullify_token": "secret-token",
    }
    base.update(overrides)
    return Config(**base)


@patch("cartography.intel.nullify.tenant.sync")
def test_skips_when_token_missing(mock_tenant_sync):
    neo4j_session = MagicMock()
    start_nullify_ingestion(neo4j_session, _config(nullify_token=None))
    mock_tenant_sync.assert_not_called()


@patch("cartography.intel.nullify.tenant.sync")
def test_skips_when_tenant_missing(mock_tenant_sync):
    neo4j_session = MagicMock()
    start_nullify_ingestion(neo4j_session, _config(nullify_tenant=None))
    mock_tenant_sync.assert_not_called()


@patch("cartography.intel.nullify.findings.sync_cspm_findings")
@patch("cartography.intel.nullify.findings.sync_secret_findings")
@patch("cartography.intel.nullify.findings.sync_container_findings")
@patch("cartography.intel.nullify.findings.sync_dependency_findings")
@patch("cartography.intel.nullify.findings.sync_sast_findings")
@patch("cartography.intel.nullify.repositories.sync")
@patch("cartography.intel.nullify.users.sync")
@patch("cartography.intel.nullify.teams.sync")
@patch("cartography.intel.nullify.tenant.sync")
def test_runs_when_configured(
    mock_tenant_sync,
    mock_teams,
    mock_users,
    mock_repos,
    mock_sast,
    mock_dependency,
    mock_container,
    mock_secret,
    mock_cspm,
):
    # All network-facing syncs are mocked so this exercises orchestration only, with
    # no real HTTP (every finding type must be patched, not just SAST).
    neo4j_session = MagicMock()
    start_nullify_ingestion(neo4j_session, _config())
    mock_tenant_sync.assert_called_once()
    mock_repos.assert_called_once()
    mock_users.assert_called_once()
    mock_teams.assert_called_once()
    mock_sast.assert_called_once()
    mock_dependency.assert_called_once()
    mock_container.assert_called_once()
    mock_secret.assert_called_once()
    mock_cspm.assert_called_once()


@patch("cartography.intel.nullify.findings.sync_cspm_findings")
@patch("cartography.intel.nullify.findings.sync_secret_findings")
@patch("cartography.intel.nullify.findings.sync_container_findings")
@patch("cartography.intel.nullify.findings.sync_dependency_findings")
@patch("cartography.intel.nullify.findings.sync_sast_findings")
@patch("cartography.intel.nullify.repositories.sync")
@patch("cartography.intel.nullify.users.sync")
@patch("cartography.intel.nullify.teams.sync")
@patch("cartography.intel.nullify.tenant.sync")
def test_bad_envelope_is_isolated(
    mock_tenant_sync,
    mock_teams,
    mock_users,
    mock_repos,
    mock_sast,
    mock_dependency,
    mock_container,
    mock_secret,
    mock_cspm,
):
    # A malformed response envelope in one resource must be isolated by _run: the module
    # keeps going and the remaining resources still sync.
    mock_repos.side_effect = NullifyEnvelopeError("boom")
    neo4j_session = MagicMock()

    start_nullify_ingestion(neo4j_session, _config())

    mock_repos.assert_called_once()
    mock_users.assert_called_once()
    mock_teams.assert_called_once()
    mock_sast.assert_called_once()
    mock_cspm.assert_called_once()
