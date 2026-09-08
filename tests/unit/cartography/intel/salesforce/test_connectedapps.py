from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.salesforce import connectedapps


def _query_error(error_code: str, object_name: str) -> requests.HTTPError:
    message = f"sObject type '{object_name}' is not supported."
    response = MagicMock(status_code=400, text=message)
    response.json.return_value = [
        {"message": message, "errorCode": error_code},
    ]
    return requests.HTTPError(
        f"Salesforce query failed with HTTP 400: {error_code}: {message}",
        response=response,
    )


def _unstructured_error() -> requests.HTTPError:
    response = MagicMock(status_code=502, text="Bad Gateway")
    response.json.side_effect = ValueError
    return requests.HTTPError("502 Server Error", response=response)


@patch.object(connectedapps, "cleanup")
@patch.object(connectedapps, "load_connected_apps")
@pytest.mark.parametrize(
    "error_code",
    ["INVALID_TYPE", "INSUFFICIENT_ACCESS_OR_READONLY"],
)
def test_sync_skips_cleanup_when_connected_apps_are_inaccessible(
    mock_load, mock_cleanup, error_code, caplog
):
    # Arrange
    client = MagicMock()
    client.query_all.side_effect = _query_error(error_code, "ConnectedApplication")

    # Act
    connectedapps.sync(
        MagicMock(),
        client,
        {"ORG_ID": "00D000000000001", "UPDATE_TAG": 123456789},
    )

    # Assert
    mock_load.assert_not_called()
    mock_cleanup.assert_not_called()
    assert "Skipping Salesforce connected apps" in caplog.text


@patch.object(connectedapps, "cleanup")
@patch.object(connectedapps, "load_connected_apps")
def test_sync_skips_entire_stage_when_oauth_tokens_are_inaccessible(
    mock_load, mock_cleanup
):
    # Arrange
    client = MagicMock()
    client.query_all.side_effect = [
        [{"Id": "0Ci000000000001AAA", "Name": "Example"}],
        _query_error("INVALID_TYPE", "OAuthToken"),
    ]

    # Act
    connectedapps.sync(
        MagicMock(),
        client,
        {"ORG_ID": "00D000000000001", "UPDATE_TAG": 123456789},
    )

    # Assert
    assert client.query_all.call_count == 2
    mock_load.assert_not_called()
    mock_cleanup.assert_not_called()


@pytest.mark.parametrize(
    "error",
    [_query_error("MALFORMED_QUERY", "ConnectedApplication"), _unstructured_error()],
)
def test_sync_raises_unexpected_query_errors(error):
    # Arrange
    client = MagicMock()
    client.query_all.side_effect = error

    # Act and assert
    with pytest.raises(requests.HTTPError):
        connectedapps.sync(
            MagicMock(),
            client,
            {"ORG_ID": "00D000000000001", "UPDATE_TAG": 123456789},
        )
