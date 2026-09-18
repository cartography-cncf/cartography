from unittest.mock import Mock
from unittest.mock import patch

from cartography.intel.socketdev import alerts


@patch("cartography.intel.socketdev.alerts.requests.get")
def test_get_requests_socket_maximum_page_size(mock_get: Mock) -> None:
    # Arrange
    mock_get.return_value.json.return_value = {
        "items": [{"id": "alert-1"}],
        "endCursor": None,
    }

    # Act
    result = alerts.get("token", "org")

    # Assert
    assert result == [{"id": "alert-1"}]
    assert mock_get.call_args.kwargs["params"] == {"per_page": 5000}
