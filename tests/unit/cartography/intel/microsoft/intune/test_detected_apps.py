import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from kiota_abstractions.api_error import APIError
from msgraph.generated.models.detected_app import DetectedApp
from msgraph.generated.models.managed_device import ManagedDevice

import cartography.intel.microsoft.intune.detected_apps
from cartography.intel.microsoft.intune.detected_apps import get_detected_apps
from cartography.intel.microsoft.intune.detected_apps import (
    get_managed_device_ids_for_detected_app,
)
from cartography.intel.microsoft.intune.detected_apps import sync_detected_apps


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


async def _mock_get_detected_apps_for_throttle_test(_client):
    yield DetectedApp(id="app-001", display_name="Google Chrome", device_count=1)


async def _mock_get_managed_device_ids_for_detected_app_throttled(
    _client,
    _detected_app_id,
):
    if False:
        yield ""
    raise APIError(
        message="Too Many Requests",
        response_status_code=429,
        response_headers={
            "Retry-After": "17",
            "request-id": "req-123",
            "client-request-id": "client-456",
            "x-ms-throttle-scope": "Tenant_Application/ReadWrite/17s",
            "x-ms-throttle-information": "ResourceUnitLimitExceeded",
        },
    )


@patch.object(
    cartography.intel.microsoft.intune.detected_apps,
    "cleanup_detected_app_relationships",
)
@patch.object(
    cartography.intel.microsoft.intune.detected_apps,
    "cleanup_detected_app_nodes",
)
@patch.object(
    cartography.intel.microsoft.intune.detected_apps,
    "load_detected_app_relationships",
)
@patch.object(
    cartography.intel.microsoft.intune.detected_apps,
    "load_detected_app_nodes",
)
@patch.object(
    cartography.intel.microsoft.intune.detected_apps,
    "get_managed_device_ids_for_detected_app",
    side_effect=_mock_get_managed_device_ids_for_detected_app_throttled,
)
@patch.object(
    cartography.intel.microsoft.intune.detected_apps,
    "get_detected_apps",
    side_effect=_mock_get_detected_apps_for_throttle_test,
)
@pytest.mark.asyncio
async def test_sync_detected_apps_logs_throttle_metadata_when_retries_are_exhausted(
    _mock_get_detected_apps,
    _mock_get_managed_device_ids,
    mock_load_detected_app_nodes,
    mock_load_detected_app_relationships,
    _mock_cleanup_detected_app_nodes,
    _mock_cleanup_detected_app_relationships,
    caplog,
):
    with caplog.at_level(
        logging.WARNING,
        logger="cartography.intel.microsoft.intune.detected_apps",
    ):
        await sync_detected_apps(
            neo4j_session=MagicMock(),
            client=MagicMock(),
            tenant_id="tenant-123",
            update_tag=1234567890,
            common_job_parameters={
                "UPDATE_TAG": 1234567890,
                "TENANT_ID": "tenant-123",
            },
        )

    assert mock_load_detected_app_nodes.called
    assert not mock_load_detected_app_relationships.called
    assert (
        "status=429, retry_after=17, request_id=req-123, "
        "client_request_id=client-456, "
        "throttle_scope=Tenant_Application/ReadWrite/17s, "
        "throttle_information=ResourceUnitLimitExceeded"
    ) in caplog.text
