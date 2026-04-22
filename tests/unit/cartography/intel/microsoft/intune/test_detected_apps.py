from typing import cast
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import cartography.intel.microsoft.intune.detected_apps
from cartography.intel.microsoft.intune.detected_apps import APPINVAGGREGATE_COLUMNS
from cartography.intel.microsoft.intune.detected_apps import APPINVRAWDATA_COLUMNS
from cartography.intel.microsoft.intune.detected_apps import sync_detected_apps
from cartography.intel.microsoft.intune.reports import ExportedReportRows
from tests.data.microsoft.intune.detected_apps import MOCK_DETECTED_APP_AGGREGATE_ROWS


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

    assert mock_load_detected_app_nodes.called
    assert not mock_load_detected_app_relationships.called
    assert not mock_cleanup_detected_app_nodes.called
    assert not mock_cleanup_detected_app_relationships.called
