from typing import Any
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from cartography.intel.kandji.devices import get


@pytest.fixture  # type: ignore[misc]
def mock_device_data_page1() -> list[dict[str, Any]]:
    return [
        {
            "device_id": str(i),
            "serial_number": f"SN{i:03d}",
            "name": f"Test Device {i}",
            "platform": "macOS",
        }
        for i in range(300)
    ]


@pytest.fixture  # type: ignore[misc]
def mock_device_data_page2() -> list[dict[str, Any]]:
    return [
        {
            "device_id": str(i),
            "serial_number": f"SN{i:03d}",
            "name": f"Test Device {i}",
            "platform": "macOS",
        }
        for i in range(300, 305)
    ]


@pytest.fixture  # type: ignore[misc]
def mock_empty_response() -> Mock:
    mock = Mock()
    mock.json.return_value = []
    mock.raise_for_status.return_value = None
    return mock


@patch("cartography.intel.kandji.devices.Session")
def test_get_devices_single_page(
    mock_session: Mock,
    mock_device_data_page1: list[dict[str, Any]],
    mock_empty_response: Mock,
) -> None:
    # Arrange
    mock_session.return_value.get.side_effect = [
        Mock(json=lambda: mock_device_data_page1, raise_for_status=lambda: None),
        mock_empty_response,
    ]
    base_uri = "https://test.kandji.io"
    token = "test-token"

    # Act
    result = get(base_uri, token)

    # Assert
    assert len(result) == 300
    assert result == mock_device_data_page1
    # Called twice: once for data, once for empty response
    assert mock_session.return_value.get.call_count == 2


@patch("cartography.intel.kandji.devices.Session")
def test_get_devices_with_pagination(
    mock_session: Mock,
    mock_device_data_page1: list[dict[str, Any]],
    mock_device_data_page2: list[dict[str, Any]],
    mock_empty_response: Mock,
) -> None:
    # Arrange
    # Map of offset to mock response
    mock_responses = {
        0: Mock(json=lambda: mock_device_data_page1, raise_for_status=lambda: None),
        300: Mock(json=lambda: mock_device_data_page2, raise_for_status=lambda: None),
    }
    mock_session.return_value.get.side_effect = (
        lambda *args, **kwargs: mock_responses.get(
            kwargs.get("params", {}).get("offset", 0),
            mock_empty_response,
        )
    )
    base_uri = "https://test.kandji.io"
    token = "test-token"

    # Act
    result = get(base_uri, token)

    # Assert that we return all the mock devices
    assert len(result) == 305
    assert result == mock_device_data_page1 + mock_device_data_page2
    # Called three times: twice for data, once for empty response
    assert mock_session.return_value.get.call_count == 3
