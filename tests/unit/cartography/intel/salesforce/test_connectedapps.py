from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.salesforce import connectedapps
from cartography.intel.salesforce.util import SalesforceQueryError


def _query_error(error_code: str) -> SalesforceQueryError:
    response = MagicMock(status_code=400, text="")
    response.json.return_value = [
        {"message": "Synthetic Salesforce error", "errorCode": error_code},
    ]
    return SalesforceQueryError(response)


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
    client.query_all.side_effect = _query_error(error_code)

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


def test_sync_raises_unexpected_query_errors():
    # Arrange
    client = MagicMock()
    client.query_all.side_effect = _query_error("MALFORMED_QUERY")

    # Act and assert
    with pytest.raises(SalesforceQueryError, match="MALFORMED_QUERY"):
        connectedapps.sync(
            MagicMock(),
            client,
            {"ORG_ID": "00D000000000001", "UPDATE_TAG": 123456789},
        )
