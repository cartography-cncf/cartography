import io
import zipfile
from types import SimpleNamespace
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from msgraph.generated.models.device_management_export_job import (
    DeviceManagementExportJob,
)
from msgraph.generated.models.device_management_report_status import (
    DeviceManagementReportStatus,
)

import cartography.intel.microsoft.intune.reports
from cartography.intel.microsoft.intune.reports import download_export_report_rows
from cartography.intel.microsoft.intune.reports import export_report_rows
from cartography.intel.microsoft.intune.reports import wait_for_export_job


def _build_zip_csv(contents: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("report.csv", contents)
    return buffer.getvalue()


@pytest.mark.asyncio
@patch(
    "cartography.intel.microsoft.intune.reports.asyncio.sleep",
    new=AsyncMock(),
)
async def test_wait_for_export_job_polls_until_completed():
    client = MagicMock()
    item_builder = (
        client.device_management.reports.export_jobs.by_device_management_export_job_id.return_value
    )
    item_builder.get = AsyncMock(
        side_effect=[
            DeviceManagementExportJob(status=DeviceManagementReportStatus.InProgress),
            DeviceManagementExportJob(
                status=DeviceManagementReportStatus.Completed,
                url="https://example.test/report.zip",
            ),
        ],
    )

    result = await wait_for_export_job(
        client,
        "job-123",
        "AppInvAggregate",
        poll_interval_seconds=0,
        timeout_seconds=5,
    )

    assert result.url == "https://example.test/report.zip"
    assert item_builder.get.await_count == 2


@pytest.mark.asyncio
@patch(
    "cartography.intel.microsoft.intune.reports.asyncio.sleep",
    new=AsyncMock(),
)
async def test_wait_for_export_job_times_out():
    client = MagicMock()
    item_builder = (
        client.device_management.reports.export_jobs.by_device_management_export_job_id.return_value
    )
    item_builder.get = AsyncMock(
        return_value=DeviceManagementExportJob(
            status=DeviceManagementReportStatus.InProgress,
        ),
    )

    with pytest.raises(
        TimeoutError,
        match="Timed out waiting for export job job-123 for AppInvAggregate",
    ):
        await wait_for_export_job(
            client,
            "job-123",
            "AppInvAggregate",
            poll_interval_seconds=0,
            timeout_seconds=0,
        )


def test_download_export_report_rows_parses_csv_zip():
    response = SimpleNamespace(
        content=_build_zip_csv(
            "ApplicationKey,ApplicationName,DeviceCount\n" "4f5c,Google Chrome,2\n"
        ),
        raise_for_status=lambda: None,
    )

    with patch.object(
        cartography.intel.microsoft.intune.reports.requests,
        "get",
        return_value=response,
    ) as mock_get:
        result = download_export_report_rows(
            "https://example.test/report.zip",
            "AppInvAggregate",
        )

    mock_get.assert_called_once()
    assert result.fieldnames == ("ApplicationKey", "ApplicationName", "DeviceCount")
    assert result.rows == [
        {
            "ApplicationKey": "4f5c",
            "ApplicationName": "Google Chrome",
            "DeviceCount": "2",
        },
    ]


@pytest.mark.asyncio
@patch.object(
    cartography.intel.microsoft.intune.reports,
    "download_export_report_rows",
)
@patch.object(
    cartography.intel.microsoft.intune.reports,
    "wait_for_export_job",
    new_callable=AsyncMock,
)
async def test_export_report_rows_creates_job_and_downloads_rows(
    mock_wait_for_export_job,
    mock_download_export_report_rows,
):
    client = MagicMock()
    export_jobs_builder = client.device_management.reports.export_jobs
    export_jobs_builder.post = AsyncMock(
        return_value=DeviceManagementExportJob(id="job-123"),
    )
    mock_wait_for_export_job.return_value = DeviceManagementExportJob(
        id="job-123",
        status=DeviceManagementReportStatus.Completed,
        url="https://example.test/report.zip",
    )
    mock_download_export_report_rows.return_value = MagicMock()

    result = await export_report_rows(
        client,
        "AppInvAggregate",
        ["ApplicationKey", "ApplicationName"],
    )

    export_jobs_builder.post.assert_awaited_once()
    created_job = export_jobs_builder.post.await_args.args[0]
    assert created_job.report_name == "AppInvAggregate"
    assert created_job.select == ["ApplicationKey", "ApplicationName"]
    mock_wait_for_export_job.assert_awaited_once_with(
        client,
        "job-123",
        "AppInvAggregate",
        poll_interval_seconds=5,
        timeout_seconds=300,
    )
    mock_download_export_report_rows.assert_called_once_with(
        "https://example.test/report.zip",
        "AppInvAggregate",
    )
    assert result is mock_download_export_report_rows.return_value
