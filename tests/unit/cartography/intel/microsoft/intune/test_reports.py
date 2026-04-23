import io
import zipfile
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


def _build_zip(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path, contents in files.items():
            archive.writestr(path, contents)
    return buffer.getvalue()


def _mock_streaming_response(content: bytes) -> MagicMock:
    response = MagicMock()
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    response.iter_content.return_value = [content]
    response.raise_for_status.return_value = None
    return response


def _mock_retryable_session(response: MagicMock) -> MagicMock:
    session = MagicMock()
    session.__enter__.return_value = session
    session.__exit__.return_value = False
    session.get.return_value = response
    return session


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


def test_download_export_report_rows_parses_csv_zip_and_preserves_missing_optionals():
    response = _mock_streaming_response(
        _build_zip(
            {
                "report.csv": (
                    "ApplicationKey,ApplicationName,ApplicationId\n"
                    "4f5c,Google Chrome,\n"
                ),
            },
        ),
    )
    session = _mock_retryable_session(response)

    with patch.object(
        cartography.intel.microsoft.intune.reports,
        "_build_retryable_session",
        return_value=session,
    ) as mock_build_session:
        result = download_export_report_rows(
            "https://example.test/report.zip",
            "AppInvAggregate",
        )

    mock_build_session.assert_called_once_with()
    session.get.assert_called_once_with(
        "https://example.test/report.zip",
        stream=True,
        timeout=60,
    )
    assert result.fieldnames == ("ApplicationKey", "ApplicationName", "ApplicationId")
    assert result.rows == [
        {
            "ApplicationKey": "4f5c",
            "ApplicationName": "Google Chrome",
            "ApplicationId": None,
        },
    ]


def test_download_export_report_rows_rejects_multiple_csv_members():
    response = _mock_streaming_response(
        _build_zip(
            {
                "report-a.csv": "ApplicationKey\n4f5c\n",
                "report-b.csv": "ApplicationKey\n4f5d\n",
            },
        ),
    )
    session = _mock_retryable_session(response)

    with patch.object(
        cartography.intel.microsoft.intune.reports,
        "_build_retryable_session",
        return_value=session,
    ):
        with pytest.raises(
            ValueError,
            match="AppInvAggregate must contain exactly one CSV file",
        ):
            download_export_report_rows(
                "https://example.test/report.zip",
                "AppInvAggregate",
            )


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
