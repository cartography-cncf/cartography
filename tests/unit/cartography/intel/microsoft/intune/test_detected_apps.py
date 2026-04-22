from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.microsoft.intune.detected_apps
from cartography.intel.microsoft.intune.detected_apps import APPINVAGGREGATE_COLUMNS
from cartography.intel.microsoft.intune.detected_apps import APPINVRAWDATA_COLUMNS
from cartography.intel.microsoft.intune.detected_apps import sync_detected_apps
from cartography.intel.microsoft.intune.detected_apps import transform_detected_app
from cartography.intel.microsoft.intune.detected_apps import (
    transform_detected_app_relationship,
)
from cartography.intel.microsoft.intune.reports import ExportedReportRows
from tests.data.microsoft.intune.detected_apps import MOCK_DETECTED_APP_AGGREGATE_ROWS
from tests.data.microsoft.intune.detected_apps import MOCK_DETECTED_APP_RAW_ROWS


def test_transform_detected_app_uses_application_key_identity():
    result = transform_detected_app(MOCK_DETECTED_APP_AGGREGATE_ROWS[0])

    assert result == {
        "id": "4f5cf2a0a1c0f5b9d4601f6ca58f5a0c9b5d77e11c1f",
        "application_id": None,
        "display_name": "Google Chrome",
        "version": "123.0.6312.86",
        "size_in_byte": None,
        "device_count": 2,
        "publisher": "Google LLC",
        "platform": "macOS",
    }


def test_transform_detected_app_relationship_uses_application_key_and_device_id():
    result = transform_detected_app_relationship(MOCK_DETECTED_APP_RAW_ROWS[0])

    assert result == {
        "app_id": "4f5cf2a0a1c0f5b9d4601f6ca58f5a0c9b5d77e11c1f",
        "device_id": "device-001",
    }


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
    "get_detected_app_raw_rows",
    new=AsyncMock(
        return_value=ExportedReportRows(
            fieldnames=tuple(APPINVRAWDATA_COLUMNS),
            rows=MOCK_DETECTED_APP_RAW_ROWS,
        ),
    ),
)
@patch.object(
    cartography.intel.microsoft.intune.detected_apps,
    "get_detected_app_aggregate_rows",
    new=AsyncMock(
        return_value=ExportedReportRows(
            fieldnames=tuple(APPINVAGGREGATE_COLUMNS),
            rows=MOCK_DETECTED_APP_AGGREGATE_ROWS,
        ),
    ),
)
@pytest.mark.asyncio
async def test_sync_detected_apps_loads_report_rows(
    mock_load_detected_app_nodes,
    mock_load_detected_app_relationships,
    mock_cleanup_detected_app_nodes,
    mock_cleanup_detected_app_relationships,
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

    mock_load_detected_app_nodes.assert_called_once_with(
        mock_load_detected_app_nodes.call_args.args[0],
        [
            {
                "id": "4f5cf2a0a1c0f5b9d4601f6ca58f5a0c9b5d77e11c1f",
                "application_id": None,
                "display_name": "Google Chrome",
                "version": "123.0.6312.86",
                "size_in_byte": None,
                "device_count": 2,
                "publisher": "Google LLC",
                "platform": "macOS",
            },
            {
                "id": "da8ab4f0d2cfe2bb9486778d6a628673da7a6e20b1dd",
                "application_id": "windows-store-app-002",
                "display_name": "Tailscale",
                "version": "1.62.0",
                "size_in_byte": None,
                "device_count": 1,
                "publisher": "Tailscale Inc.",
                "platform": "macOS",
            },
        ],
        "tenant-123",
        1234567890,
    )
    mock_load_detected_app_relationships.assert_called_once_with(
        mock_load_detected_app_relationships.call_args.args[0],
        [
            {
                "app_id": "4f5cf2a0a1c0f5b9d4601f6ca58f5a0c9b5d77e11c1f",
                "device_id": "device-001",
            },
            {
                "app_id": "4f5cf2a0a1c0f5b9d4601f6ca58f5a0c9b5d77e11c1f",
                "device_id": "device-002",
            },
            {
                "app_id": "da8ab4f0d2cfe2bb9486778d6a628673da7a6e20b1dd",
                "device_id": "device-001",
            },
        ],
        "tenant-123",
        1234567890,
    )
    mock_cleanup_detected_app_nodes.assert_called_once()
    mock_cleanup_detected_app_relationships.assert_called_once()


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
    "get_detected_app_raw_rows",
    new=AsyncMock(
        return_value=ExportedReportRows(
            fieldnames=("ApplicationKey",),
            rows=[],
        ),
    ),
)
@patch.object(
    cartography.intel.microsoft.intune.detected_apps,
    "get_detected_app_aggregate_rows",
    new=AsyncMock(
        return_value=ExportedReportRows(
            fieldnames=tuple(APPINVAGGREGATE_COLUMNS),
            rows=MOCK_DETECTED_APP_AGGREGATE_ROWS,
        ),
    ),
)
@pytest.mark.asyncio
async def test_sync_detected_apps_raises_on_missing_required_columns(
    mock_load_detected_app_nodes,
    mock_load_detected_app_relationships,
    mock_cleanup_detected_app_nodes,
    mock_cleanup_detected_app_relationships,
):
    with pytest.raises(
        ValueError,
        match="AppInvRawData export is missing required columns: DeviceId",
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
    assert not mock_cleanup_detected_app_nodes.called
    assert not mock_cleanup_detected_app_relationships.called


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
    "get_detected_app_raw_rows",
    new=AsyncMock(
        return_value=ExportedReportRows(
            fieldnames=tuple(APPINVRAWDATA_COLUMNS),
            rows=[
                {
                    "ApplicationKey": "4f5cf2a0a1c0f5b9d4601f6ca58f5a0c9b5d77e11c1f",
                    "DeviceId": "",
                },
            ],
        ),
    ),
)
@patch.object(
    cartography.intel.microsoft.intune.detected_apps,
    "get_detected_app_aggregate_rows",
    new=AsyncMock(
        return_value=ExportedReportRows(
            fieldnames=tuple(APPINVAGGREGATE_COLUMNS),
            rows=MOCK_DETECTED_APP_AGGREGATE_ROWS,
        ),
    ),
)
@pytest.mark.asyncio
async def test_sync_detected_apps_raises_on_malformed_rows_and_skips_cleanup(
    mock_load_detected_app_nodes,
    mock_load_detected_app_relationships,
    mock_cleanup_detected_app_nodes,
    mock_cleanup_detected_app_relationships,
):
    with pytest.raises(
        ValueError,
        match="AppInvRawData row is missing required value for DeviceId",
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
    assert not mock_cleanup_detected_app_nodes.called
    assert not mock_cleanup_detected_app_relationships.called
