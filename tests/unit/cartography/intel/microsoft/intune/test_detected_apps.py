from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from kiota_abstractions.api_error import APIError
from msgraph.generated.models.detected_app import DetectedApp
from msgraph.generated.models.managed_device import ManagedDevice

from cartography.intel.microsoft.intune.detected_apps import get_detected_apps


@pytest.mark.asyncio
async def test_get_detected_apps_falls_back_to_per_app_lookup_when_expand_is_empty():
    app = DetectedApp(
        id="app-001",
        display_name="Google Chrome",
        device_count=2,
        managed_devices=[],
    )
    app_page = SimpleNamespace(value=[app], odata_next_link=None)
    managed_devices_page = SimpleNamespace(
        value=[ManagedDevice(id="device-001"), ManagedDevice(id="device-002")],
        odata_next_link=None,
    )

    client = MagicMock()
    detected_apps_builder = client.device_management.detected_apps
    detected_apps_builder.DetectedAppsRequestBuilderGetRequestConfiguration = (
        lambda query_parameters: query_parameters
    )
    detected_apps_builder.DetectedAppsRequestBuilderGetQueryParameters = (
        lambda **kwargs: kwargs
    )
    detected_apps_builder.get = AsyncMock(return_value=app_page)

    managed_devices_builder = (
        detected_apps_builder.by_detected_app_id.return_value.managed_devices
    )
    managed_devices_builder.ManagedDevicesRequestBuilderGetRequestConfiguration = (
        lambda query_parameters: query_parameters
    )
    managed_devices_builder.ManagedDevicesRequestBuilderGetQueryParameters = (
        lambda **kwargs: kwargs
    )
    managed_devices_builder.get = AsyncMock(return_value=managed_devices_page)

    result = [detected_app async for detected_app in get_detected_apps(client)]

    assert len(result) == 1
    assert [device.id for device in result[0].managed_devices] == [
        "device-001",
        "device-002",
    ]
    detected_apps_builder.by_detected_app_id.assert_called_once_with("app-001")


@pytest.mark.asyncio
async def test_get_detected_apps_continues_when_per_app_lookup_fails():
    app = DetectedApp(
        id="app-001",
        display_name="Google Chrome",
        device_count=2,
        managed_devices=[],
    )
    app_page = SimpleNamespace(value=[app], odata_next_link=None)

    client = MagicMock()
    detected_apps_builder = client.device_management.detected_apps
    detected_apps_builder.DetectedAppsRequestBuilderGetRequestConfiguration = (
        lambda query_parameters: query_parameters
    )
    detected_apps_builder.DetectedAppsRequestBuilderGetQueryParameters = (
        lambda **kwargs: kwargs
    )
    detected_apps_builder.get = AsyncMock(return_value=app_page)

    managed_devices_builder = (
        detected_apps_builder.by_detected_app_id.return_value.managed_devices
    )
    managed_devices_builder.ManagedDevicesRequestBuilderGetRequestConfiguration = (
        lambda query_parameters: query_parameters
    )
    managed_devices_builder.ManagedDevicesRequestBuilderGetQueryParameters = (
        lambda **kwargs: kwargs
    )

    error = APIError("fallback failed")
    error.response_status_code = 500
    managed_devices_builder.get = AsyncMock(side_effect=error)

    result = [detected_app async for detected_app in get_detected_apps(client)]

    assert len(result) == 1
    assert result[0].managed_devices == []
    detected_apps_builder.by_detected_app_id.assert_called_once_with("app-001")
