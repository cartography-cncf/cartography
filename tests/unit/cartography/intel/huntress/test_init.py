from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from cartography.config import Config
from cartography.intel.huntress import DEFAULT_BASE_URI
from cartography.intel.huntress import start_huntress_ingestion

TEST_ACCOUNT_ID = 1000


def _config(**overrides: object) -> Config:
    values: dict[str, object] = {
        "huntress_base_uri": None,
        "huntress_api_key": "hk_0123456789abcdef",
        "huntress_api_secret": "hs_fedcba9876543210",
        "update_tag": 123456789,
    }
    values.update(overrides)
    return cast(Config, SimpleNamespace(**values))


@patch("cartography.intel.huntress.memberships.sync")
@patch("cartography.intel.huntress.incident_reports.sync")
@patch("cartography.intel.huntress.agents.sync")
@patch("cartography.intel.huntress.organizations.sync")
@patch("cartography.intel.huntress.account.sync", return_value=TEST_ACCOUNT_ID)
@patch("cartography.intel.huntress.create_huntress_api_session")
def test_start_huntress_ingestion_uses_shared_api_session(
    mock_create_api_session: Mock,
    mock_account_sync: Mock,
    mock_organizations_sync: Mock,
    mock_agents_sync: Mock,
    mock_incident_reports_sync: Mock,
    mock_memberships_sync: Mock,
) -> None:
    mock_api_session = MagicMock()
    mock_create_api_session.return_value = mock_api_session

    start_huntress_ingestion(MagicMock(), _config())

    mock_create_api_session.assert_called_once_with(
        "hk_0123456789abcdef",
        "hs_fedcba9876543210",
    )
    for mock_sync in (
        mock_organizations_sync,
        mock_agents_sync,
        mock_incident_reports_sync,
        mock_memberships_sync,
    ):
        mock_sync.assert_called_once()
        assert mock_sync.call_args.args[1] is mock_api_session
        assert mock_sync.call_args.args[2] == DEFAULT_BASE_URI
        # The account resolved from the API scopes every downstream sync.
        assert mock_sync.call_args.args[3] == TEST_ACCOUNT_ID
        assert mock_sync.call_args.args[5]["ACCOUNT_ID"] == TEST_ACCOUNT_ID
    mock_api_session.close.assert_called_once_with()


@patch("cartography.intel.huntress.memberships.sync")
@patch("cartography.intel.huntress.incident_reports.sync")
@patch("cartography.intel.huntress.agents.sync")
@patch("cartography.intel.huntress.organizations.sync")
@patch("cartography.intel.huntress.account.sync", return_value=TEST_ACCOUNT_ID)
@patch("cartography.intel.huntress.create_huntress_api_session")
def test_start_huntress_ingestion_honors_a_custom_base_uri(
    mock_create_api_session: Mock,
    mock_account_sync: Mock,
    mock_organizations_sync: Mock,
    mock_agents_sync: Mock,
    mock_incident_reports_sync: Mock,
    mock_memberships_sync: Mock,
) -> None:
    start_huntress_ingestion(
        MagicMock(),
        _config(huntress_base_uri="https://api.eu.huntress.io"),
    )

    assert mock_account_sync.call_args.args[2] == "https://api.eu.huntress.io"
    assert mock_agents_sync.call_args.args[2] == "https://api.eu.huntress.io"


@patch(
    "cartography.intel.huntress.organizations.sync", side_effect=RuntimeError("boom")
)
@patch("cartography.intel.huntress.account.sync", return_value=TEST_ACCOUNT_ID)
@patch("cartography.intel.huntress.create_huntress_api_session")
def test_start_huntress_ingestion_closes_the_session_on_error(
    mock_create_api_session: Mock,
    mock_account_sync: Mock,
    mock_organizations_sync: Mock,
) -> None:
    mock_api_session = MagicMock()
    mock_create_api_session.return_value = mock_api_session

    with pytest.raises(RuntimeError):
        start_huntress_ingestion(MagicMock(), _config())

    mock_api_session.close.assert_called_once_with()


@pytest.mark.parametrize(
    "overrides",
    [
        {"huntress_api_key": None},
        {"huntress_api_secret": None},
        {"huntress_api_key": None, "huntress_api_secret": None},
    ],
)
@patch("cartography.intel.huntress.create_huntress_api_session")
def test_start_huntress_ingestion_skips_without_both_credentials(
    mock_create_api_session,
    overrides,
):
    start_huntress_ingestion(MagicMock(), _config(**overrides))

    mock_create_api_session.assert_not_called()
