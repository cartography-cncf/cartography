from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from msgraph.generated.models.detected_app import DetectedApp
from msgraph.generated.models.managed_device import ManagedDevice

from cartography.intel.microsoft.intune.detected_apps import get_detected_apps
from cartography.intel.microsoft.intune.detected_apps import (
    get_managed_device_ids_for_detected_app,
)


@pytest.mark.asyncio
async def test_get_detected_apps_uses_lightweight_query_and_clears_pages():
    first_page = SimpleNamespace(
        value=[DetectedApp(id="app-001", display_name="Google Chrome")],
        odata_next_link="next-link",
    )
    second_page = SimpleNamespace(
        value=[DetectedApp(id="app-002", display_name="Tailscale")],
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
    detected_apps_builder.get = AsyncMock(return_value=first_page)
    detected_apps_builder.with_url.return_value.get = AsyncMock(
        return_value=second_page
    )

    result = [detected_app async for detected_app in get_detected_apps(client)]

    assert [app.id for app in result] == ["app-001", "app-002"]
    assert detected_apps_builder.get.await_args.kwargs["request_configuration"] == {
        "select": [
            "id",
            "displayName",
            "version",
            "sizeInByte",
            "deviceCount",
            "publisher",
            "platform",
        ],
        "top": 50,
    }
    assert first_page.value is None
    detected_apps_builder.with_url.assert_called_once_with("next-link")


@pytest.mark.asyncio
async def test_get_managed_device_ids_for_detected_app_streams_all_pages():
    first_page = SimpleNamespace(
        value=[ManagedDevice(id="device-001"), ManagedDevice(id="device-002")],
        odata_next_link="next-link",
    )
    second_page = SimpleNamespace(
        value=[ManagedDevice(id="device-003")],
        odata_next_link=None,
    )

    client = MagicMock()
    detected_apps_builder = client.device_management.detected_apps
    managed_devices_builder = (
        detected_apps_builder.by_detected_app_id.return_value.managed_devices
    )
    managed_devices_builder.ManagedDevicesRequestBuilderGetRequestConfiguration = (
        lambda query_parameters: query_parameters
    )
    managed_devices_builder.ManagedDevicesRequestBuilderGetQueryParameters = (
        lambda **kwargs: kwargs
    )
    managed_devices_builder.get = AsyncMock(return_value=first_page)
    managed_devices_builder.with_url.return_value.get = AsyncMock(
        return_value=second_page,
    )

    result = [
        device_id
        async for device_id in get_managed_device_ids_for_detected_app(
            client,
            "app-001",
        )
    ]

    detected_apps_builder.by_detected_app_id.assert_called_once_with("app-001")
    assert result == ["device-001", "device-002", "device-003"]
    assert managed_devices_builder.get.await_args.kwargs["request_configuration"] == {
        "select": ["id"],
        "top": 100,
    }
    assert first_page.value is None
    managed_devices_builder.with_url.assert_called_once_with("next-link")
