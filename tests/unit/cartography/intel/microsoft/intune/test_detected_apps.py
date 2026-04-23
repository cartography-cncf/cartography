from typing import cast
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.microsoft.intune.detected_apps
from cartography.intel.microsoft.intune.detected_apps import APPINVAGGREGATE_COLUMNS
from cartography.intel.microsoft.intune.detected_apps import APPINVRAWDATA_COLUMNS
from cartography.intel.microsoft.intune.detected_apps import (
    build_detected_app_export_rows,
)
from cartography.intel.microsoft.intune.detected_apps import sync_detected_apps
from cartography.intel.microsoft.intune.reports import ExportedReportRows
from tests.data.microsoft.intune.detected_apps import MOCK_DETECTED_APP_AGGREGATE_ROWS
from tests.data.microsoft.intune.detected_apps import MOCK_DETECTED_APP_RAW_ROWS


def test_build_detected_app_export_rows_unions_both_reports():
    apps, relationships = build_detected_app_export_rows(
        cast(list[dict[str, str | None]], MOCK_DETECTED_APP_AGGREGATE_ROWS),
        cast(list[dict[str, str | None]], MOCK_DETECTED_APP_RAW_ROWS),
    )

    assert apps == [
        {
            "id": "0142ec1846a5fe5aae49d155590a2116300000904abcd",
            "application_id": None,
            "display_name": "Microsoft Device Inventory Agent",
            "version": "26.4.20.2000",
            "device_count": 1,
            "publisher": "Microsoft Corporation",
            "platform": "Windows",
        },
        {
            "id": "4f5cf2a0a1c0f5b9d4601f6ca58f5a0c9b5d77e11c1f",
            "application_id": None,
            "display_name": "Google Chrome",
            "version": "123.0.6312.86",
            "device_count": 2,
            "publisher": "Google LLC",
            "platform": "macOS",
        },
        {
            "id": "75c4c0a1f23d4e5b98aa1274c1e0dbbb73f0fffeabcd",
            "application_id": None,
            "display_name": "Cursor (User)",
            "version": "0.45.14",
            "device_count": 1,
            "publisher": "Anysphere, Inc.",
            "platform": "Windows",
        },
        {
            "id": "da8ab4f0d2cfe2bb9486778d6a628673da7a6e20b1dd",
            "application_id": "windows-store-app-002",
            "display_name": "Tailscale",
            "version": "1.62.0",
            "device_count": 1,
            "publisher": "Tailscale Inc.",
            "platform": "macOS",
        },
    ]
    assert relationships == [
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
        {
            "app_id": "0142ec1846a5fe5aae49d155590a2116300000904abcd",
            "device_id": "device-002",
        },
    ]


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
            fieldnames=(
                "ApplicationKey",
                "ApplicationName",
                "ApplicationPublisher",
                "ApplicationVersion",
                "Platform",
            ),
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
            rows=cast(list[dict[str, str | None]], MOCK_DETECTED_APP_AGGREGATE_ROWS),
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

    assert not mock_load_detected_app_nodes.called
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
                    "ApplicationName": "Google Chrome",
                    "ApplicationPublisher": "Google LLC",
                    "ApplicationVersion": "123.0.6312.86",
                    "Platform": "macOS",
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
            rows=cast(list[dict[str, str | None]], MOCK_DETECTED_APP_AGGREGATE_ROWS),
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

    assert not mock_load_detected_app_nodes.called
    assert not mock_load_detected_app_relationships.called
    assert not mock_cleanup_detected_app_nodes.called
    assert not mock_cleanup_detected_app_relationships.called
