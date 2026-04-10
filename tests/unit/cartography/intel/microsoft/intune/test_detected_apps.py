from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from kiota_abstractions.api_error import APIError
from msgraph.generated.models.detected_app import DetectedApp
from msgraph.generated.models.managed_device import ManagedDevice

from cartography.intel.microsoft.intune.detected_apps import get_detected_apps
from cartography.intel.microsoft.intune.detected_apps import sync_detected_apps


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


@pytest.mark.asyncio
async def test_sync_detected_apps_batches_by_flattened_rows():
    app_one = DetectedApp(
        id="app-001",
        display_name="Google Chrome",
        device_count=2,
        managed_devices=[
            ManagedDevice(id="device-001"),
            ManagedDevice(id="device-002"),
        ],
    )
    app_two = DetectedApp(
        id="app-002",
        display_name="Tailscale",
        device_count=1,
        managed_devices=[ManagedDevice(id="device-003")],
    )

    async def _mock_get_detected_apps(_client):
        yield app_one
        yield app_two

    load_calls: list[list[dict[str, str | int | None]]] = []

    def _capture_load(_session, rows, _tenant_id, _update_tag):
        load_calls.append([dict(row) for row in rows])

    with (
        patch(
            "cartography.intel.microsoft.intune.detected_apps.get_detected_apps",
            side_effect=_mock_get_detected_apps,
        ),
        patch(
            "cartography.intel.microsoft.intune.detected_apps.load_detected_apps",
            side_effect=_capture_load,
        ),
        patch("cartography.intel.microsoft.intune.detected_apps.cleanup"),
        patch("cartography.intel.microsoft.intune.detected_apps.gc.collect"),
        patch(
            "cartography.intel.microsoft.intune.detected_apps.DETECTED_APP_ROW_BATCH_SIZE",
            2,
        ),
    ):
        await sync_detected_apps(
            neo4j_session=None,
            client=None,
            tenant_id="tenant-001",
            update_tag=123,
            common_job_parameters={"UPDATE_TAG": 123, "TENANT_ID": "tenant-001"},
        )

    assert load_calls == [
        [
            {
                "id": "app-001",
                "display_name": "Google Chrome",
                "version": None,
                "size_in_byte": None,
                "device_count": 2,
                "publisher": None,
                "platform": None,
                "device_id": "device-001",
            },
            {
                "id": "app-001",
                "display_name": "Google Chrome",
                "version": None,
                "size_in_byte": None,
                "device_count": 2,
                "publisher": None,
                "platform": None,
                "device_id": "device-002",
            },
        ],
        [
            {
                "id": "app-002",
                "display_name": "Tailscale",
                "version": None,
                "size_in_byte": None,
                "device_count": 1,
                "publisher": None,
                "platform": None,
                "device_id": "device-003",
            },
        ],
    ]
    assert app_one.managed_devices is None
    assert app_two.managed_devices is None
