import logging
from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

import requests

from cartography.intel.sentinelone import start_sentinelone_ingestion
from cartography.intel.sentinelone.account import SentinelOneSyncScope


def _site_scope_http_error() -> requests.HTTPError:
    response = MagicMock()
    response.status_code = 403
    response.json.return_value = {
        "errors": [
            {
                "code": 4030010,
                "detail": "Action is not allowed to site users",
            },
        ],
    }
    return requests.HTTPError(response=response)


@patch("cartography.intel.sentinelone.merge_module_sync_metadata")
@patch("cartography.intel.sentinelone.finding.cleanup")
@patch("cartography.intel.sentinelone.application.cleanup")
@patch("cartography.intel.sentinelone.agent.cleanup")
@patch("cartography.intel.sentinelone.finding.sync")
@patch("cartography.intel.sentinelone.application.sync")
@patch("cartography.intel.sentinelone.agent.sync")
@patch("cartography.intel.sentinelone.sync_site_scoped_accounts")
@patch("cartography.intel.sentinelone.sync_accounts")
def test_start_sentinelone_ingestion_falls_back_to_site_scoped_sync(
    mock_sync_accounts,
    mock_sync_site_scoped_accounts,
    mock_agent_sync,
    mock_application_sync,
    mock_finding_sync,
    mock_agent_cleanup,
    mock_application_cleanup,
    mock_finding_cleanup,
    mock_merge_metadata,
    caplog,
):
    mock_sync_accounts.side_effect = _site_scope_http_error()
    mock_sync_site_scoped_accounts.return_value = [
        SentinelOneSyncScope(account_id="account-1", site_id="site-1"),
        SentinelOneSyncScope(account_id="account-1", site_id="site-2"),
    ]
    sync_snapshots: list[dict[str, object]] = []
    sync_cleanup_args: list[bool] = []

    def capture_sync(_neo4j_session, common_job_parameters, *, do_cleanup=True):
        sync_snapshots.append(dict(common_job_parameters))
        sync_cleanup_args.append(do_cleanup)

    mock_agent_sync.side_effect = capture_sync
    mock_application_sync.side_effect = capture_sync
    mock_finding_sync.side_effect = capture_sync

    config = SimpleNamespace(
        update_tag=123456789,
        sentinelone_api_url="https://test-api.sentinelone.net",
        sentinelone_api_token="test-token",
        sentinelone_account_ids=None,
        sentinelone_site_ids=None,
    )
    neo4j_session = MagicMock()

    with caplog.at_level(logging.WARNING):
        start_sentinelone_ingestion(neo4j_session, config)

    mock_sync_accounts.assert_called_once()
    mock_sync_site_scoped_accounts.assert_called_once()
    assert (
        "SentinelOne token cannot enumerate /accounts for a site-scoped user; "
        "continuing with site-scoped sync fallback"
    ) in caplog.text

    assert mock_agent_sync.call_count == 2
    assert mock_application_sync.call_count == 2
    assert mock_finding_sync.call_count == 2

    for common_job_parameters in sync_snapshots:
        assert common_job_parameters["S1_ACCOUNT_ID"] == "account-1"
        assert common_job_parameters["S1_SITE_ID"] in {"site-1", "site-2"}

    assert len(sync_cleanup_args) == (
        mock_agent_sync.call_count
        + mock_application_sync.call_count
        + mock_finding_sync.call_count
    )
    assert all(not do_cleanup for do_cleanup in sync_cleanup_args)

    mock_agent_cleanup.assert_called_once()
    mock_application_cleanup.assert_called_once()
    mock_finding_cleanup.assert_called_once()
    mock_merge_metadata.assert_called_once()


@patch("cartography.intel.sentinelone.merge_module_sync_metadata")
@patch("cartography.intel.sentinelone.finding.cleanup")
@patch("cartography.intel.sentinelone.application.cleanup")
@patch("cartography.intel.sentinelone.agent.cleanup")
@patch("cartography.intel.sentinelone.finding.sync")
@patch("cartography.intel.sentinelone.application.sync")
@patch("cartography.intel.sentinelone.agent.sync")
@patch("cartography.intel.sentinelone.sync_site_scoped_accounts")
@patch("cartography.intel.sentinelone.sync_accounts")
def test_start_sentinelone_ingestion_prefers_explicit_site_ids(
    mock_sync_accounts,
    mock_sync_site_scoped_accounts,
    mock_agent_sync,
    mock_application_sync,
    mock_finding_sync,
    mock_agent_cleanup,
    mock_application_cleanup,
    mock_finding_cleanup,
    mock_merge_metadata,
):
    sync_cleanup_args: list[bool] = []

    def capture_sync(_neo4j_session, _common_job_parameters, *, do_cleanup=True):
        sync_cleanup_args.append(do_cleanup)

    mock_sync_site_scoped_accounts.return_value = [
        SentinelOneSyncScope(account_id="account-1", site_id="site-1"),
    ]
    mock_agent_sync.side_effect = capture_sync
    mock_application_sync.side_effect = capture_sync
    mock_finding_sync.side_effect = capture_sync
    config = SimpleNamespace(
        update_tag=123456789,
        sentinelone_api_url="https://test-api.sentinelone.net",
        sentinelone_api_token="test-token",
        sentinelone_account_ids=["account-1"],
        sentinelone_site_ids=["site-1"],
    )

    start_sentinelone_ingestion(MagicMock(), config)

    mock_sync_accounts.assert_not_called()
    mock_sync_site_scoped_accounts.assert_called_once()
    assert len(sync_cleanup_args) == 3
    assert all(not do_cleanup for do_cleanup in sync_cleanup_args)
    mock_agent_cleanup.assert_not_called()
    mock_application_cleanup.assert_not_called()
    mock_finding_cleanup.assert_not_called()
    mock_merge_metadata.assert_called_once()
