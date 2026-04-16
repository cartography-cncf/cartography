from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

from cartography.config import Config
from cartography.intel.jamf import start_jamf_ingestion


@patch("cartography.intel.jamf.computers.sync")
@patch("cartography.intel.jamf.create_jamf_api_session")
def test_start_jamf_ingestion_uses_shared_api_session(
    mock_create_jamf_api_session: Mock,
    mock_sync: Mock,
) -> None:
    mock_api_session = MagicMock()
    mock_create_jamf_api_session.return_value = mock_api_session
    config = cast(
        Config,
        SimpleNamespace(
            jamf_base_uri="https://test.jamfcloud.com/JSSResource",
            jamf_user="test-user",
            jamf_password="test-password",
            update_tag=123456789,
        ),
    )

    start_jamf_ingestion(MagicMock(), config)

    mock_create_jamf_api_session.assert_called_once_with(
        "https://test.jamfcloud.com/JSSResource",
        "test-user",
        "test-password",
    )
    mock_sync.assert_called_once()
    assert mock_sync.call_args.args[1] is mock_api_session
    mock_api_session.close.assert_called_once_with()
