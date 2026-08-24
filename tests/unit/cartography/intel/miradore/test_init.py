from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from cartography.config import Config
from cartography.intel.miradore import DEFAULT_BASE_URI
from cartography.intel.miradore import start_miradore_ingestion


def _config(**overrides: object) -> Config:
    values: dict[str, object] = {
        "miradore_base_uri": None,
        "miradore_site_name": "simpsoncorp",
        "miradore_api_key": "1_AaDf234sdf8!4",
        "update_tag": 123456789,
    }
    values.update(overrides)
    return cast(Config, SimpleNamespace(**values))


@patch("cartography.intel.miradore.devices.sync")
@patch("cartography.intel.miradore.users.sync")
@patch("cartography.intel.miradore.config_profiles.sync")
@patch("cartography.intel.miradore.tags.sync")
@patch("cartography.intel.miradore.locations.sync")
@patch("cartography.intel.miradore.organizations.sync")
@patch("cartography.intel.miradore.create_miradore_api_session")
def test_start_miradore_ingestion_uses_shared_api_session(
    mock_create_api_session: Mock,
    mock_organizations_sync: Mock,
    mock_locations_sync: Mock,
    mock_tags_sync: Mock,
    mock_config_profiles_sync: Mock,
    mock_users_sync: Mock,
    mock_devices_sync: Mock,
) -> None:
    mock_api_session = MagicMock()
    mock_create_api_session.return_value = mock_api_session

    start_miradore_ingestion(MagicMock(), _config())

    for mock_sync in (
        mock_organizations_sync,
        mock_locations_sync,
        mock_tags_sync,
        mock_config_profiles_sync,
        mock_users_sync,
        mock_devices_sync,
    ):
        mock_sync.assert_called_once()
        assert mock_sync.call_args.args[1] is mock_api_session
        assert mock_sync.call_args.args[2] == DEFAULT_BASE_URI
        assert mock_sync.call_args.args[3] == "simpsoncorp"
        assert mock_sync.call_args.args[4] == "1_AaDf234sdf8!4"
    mock_api_session.close.assert_called_once_with()


@patch("cartography.intel.miradore.devices.sync")
@patch("cartography.intel.miradore.users.sync")
@patch("cartography.intel.miradore.config_profiles.sync")
@patch("cartography.intel.miradore.tags.sync")
@patch("cartography.intel.miradore.locations.sync")
@patch("cartography.intel.miradore.organizations.sync")
@patch("cartography.intel.miradore.create_miradore_api_session")
def test_start_miradore_ingestion_honors_a_custom_base_uri(
    mock_create_api_session: Mock,
    mock_organizations_sync: Mock,
    mock_locations_sync: Mock,
    mock_tags_sync: Mock,
    mock_config_profiles_sync: Mock,
    mock_users_sync: Mock,
    mock_devices_sync: Mock,
) -> None:
    mock_create_api_session.return_value = MagicMock()

    start_miradore_ingestion(
        MagicMock(),
        _config(miradore_base_uri="https://miradore.internal.example.com"),
    )

    assert (
        mock_organizations_sync.call_args.args[2]
        == "https://miradore.internal.example.com"
    )


@patch("cartography.intel.miradore.organizations.sync")
@patch("cartography.intel.miradore.create_miradore_api_session")
def test_start_miradore_ingestion_closes_session_on_sync_error(
    mock_create_api_session: Mock,
    mock_organizations_sync: Mock,
) -> None:
    mock_api_session = MagicMock()
    mock_create_api_session.return_value = mock_api_session
    mock_organizations_sync.side_effect = RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        start_miradore_ingestion(MagicMock(), _config())

    mock_api_session.close.assert_called_once_with()


@patch("cartography.intel.miradore.create_miradore_api_session")
def test_start_miradore_ingestion_skips_without_a_site_name(
    mock_create_api_session: Mock,
) -> None:
    start_miradore_ingestion(MagicMock(), _config(miradore_site_name=None))

    mock_create_api_session.assert_not_called()


@patch("cartography.intel.miradore.create_miradore_api_session")
def test_start_miradore_ingestion_skips_without_an_api_key(
    mock_create_api_session: Mock,
) -> None:
    start_miradore_ingestion(MagicMock(), _config(miradore_api_key=None))

    mock_create_api_session.assert_not_called()
