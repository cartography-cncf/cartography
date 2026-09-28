import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.salesforce import connectedapps

_CONNECTED_APP_QUERY = f"SELECT {connectedapps._APP_FIELDS} FROM ConnectedApplication"
_OAUTH_TOKEN_QUERY = "SELECT Id, AppName, UserId FROM OAuthToken"


def _query_error(
    error_code: str,
    message: str,
    soql: str = _CONNECTED_APP_QUERY,
) -> requests.HTTPError:
    request = requests.Request(
        "GET",
        "https://example.my.salesforce.com/services/data/v60.0/query",
        params={"q": soql},
    ).prepare()
    response = requests.Response()
    response.status_code = 400
    response._content = json.dumps(
        [{"message": message, "errorCode": error_code}]
    ).encode()
    response.request = request
    response.url = request.url or ""
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        return exc
    raise AssertionError("400 response did not raise")


def _unstructured_error() -> requests.HTTPError:
    response = MagicMock(status_code=502, text="Bad Gateway")
    response.json.side_effect = ValueError
    return requests.HTTPError("502 Server Error", response=response)


@patch.object(connectedapps, "cleanup")
@patch.object(connectedapps, "load_connected_apps")
@pytest.mark.parametrize(
    ("error_code", "message"),
    [
        (
            "INVALID_TYPE",
            "sObject type 'ConnectedApplication' is not supported.",
        ),
        ("INSUFFICIENT_ACCESS", "insufficient access rights on object id"),
        (
            "INSUFFICIENT_ACCESS_OR_READONLY",
            "insufficient access rights on object id",
        ),
    ],
)
def test_sync_skips_cleanup_when_connected_apps_are_inaccessible(
    mock_load, mock_cleanup, error_code, message, caplog
):
    # Arrange
    client = MagicMock()
    client.query_all.side_effect = _query_error(error_code, message)

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
def test_sync_skips_when_connected_app_setup_fields_are_hidden(
    mock_load, mock_cleanup, caplog
):
    # Arrange
    client = MagicMock()
    client.query_all.side_effect = _query_error(
        "INVALID_FIELD",
        "\nSELECT Id, Name, OptionsAllowAdminApprovedUsersOnly\n"
        "                 ^\n"
        "ERROR at Row:1:Column:18\n"
        "No such column 'OptionsAllowAdminApprovedUsersOnly' on entity "
        "'ConnectedApplication'. If you are attempting to use a custom field, "
        "be sure to append the '__c' after the custom field name.",
    )

    # Act
    connectedapps.sync(
        MagicMock(),
        client,
        {"ORG_ID": "00D000000000001", "UPDATE_TAG": 123456789},
    )

    # Assert
    mock_load.assert_not_called()
    mock_cleanup.assert_not_called()
    assert "preserving previously synced connected app data" in caplog.text
    assert "example.my.salesforce.com" not in caplog.text


@patch.object(connectedapps, "cleanup")
@patch.object(connectedapps, "load_connected_apps")
def test_sync_skips_entire_stage_when_oauth_tokens_are_inaccessible(
    mock_load, mock_cleanup
):
    # Arrange
    client = MagicMock()
    client.query_all.side_effect = [
        [{"Id": "0Ci000000000001AAA", "Name": "Example"}],
        _query_error(
            "INVALID_TYPE",
            "sObject type 'OAuthToken' is not supported.",
            _OAUTH_TOKEN_QUERY,
        ),
    ]

    # Act
    connectedapps.sync(
        MagicMock(),
        client,
        {"ORG_ID": "00D000000000001", "UPDATE_TAG": 123456789},
    )

    # Assert
    mock_load.assert_not_called()
    mock_cleanup.assert_not_called()


@pytest.mark.parametrize(
    "error",
    [
        _query_error("MALFORMED_QUERY", "unexpected token"),
        _query_error(
            "INVALID_FIELD",
            "No such column 'UnexpectedField' on entity 'ConnectedApplication'.",
        ),
        _query_error(
            "INVALID_TYPE",
            "sObject type 'UnexpectedObject' is not supported.",
        ),
        _unstructured_error(),
    ],
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
