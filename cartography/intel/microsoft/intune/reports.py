import asyncio
import csv
import io
import logging
import tempfile
import time
import zipfile
from dataclasses import dataclass

import requests
from msgraph import GraphServiceClient
from msgraph.generated.models.device_management_export_job import (
    DeviceManagementExportJob,
)
from msgraph.generated.models.device_management_report_file_format import (
    DeviceManagementReportFileFormat,
)
from msgraph.generated.models.device_management_report_status import (
    DeviceManagementReportStatus,
)
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from cartography.util import timeit

logger = logging.getLogger(__name__)

DEFAULT_REPORT_POLL_INTERVAL_SECONDS = 5
DEFAULT_REPORT_TIMEOUT_SECONDS = 300
EXPORT_DOWNLOAD_TIMEOUT_SECONDS = 60
MAX_REPORT_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_REPORT_UNCOMPRESSED_BYTES = 256 * 1024 * 1024
EXPORT_DOWNLOAD_MAX_RETRIES = 3
EXPORT_DOWNLOAD_RETRY_BACKOFF_SECONDS = 1.0
EXPORT_DOWNLOAD_RETRY_STATUS_CODES = (429, 500, 502, 503, 504)


@dataclass(frozen=True)
class ExportedReportRows:
    fieldnames: tuple[str, ...]
    # The sync pipeline needs repeated access to the same export rows when it
    # builds the union of aggregate and raw app keys. Materializing the rows
    # keeps that logic straightforward, while explicit size caps bound memory.
    rows: list[dict[str, str | None]]


@timeit
async def export_report_rows(
    client: GraphServiceClient,
    report_name: str,
    select: list[str],
    *,
    report_filter: str | None = None,
    poll_interval_seconds: int = DEFAULT_REPORT_POLL_INTERVAL_SECONDS,
    timeout_seconds: int = DEFAULT_REPORT_TIMEOUT_SECONDS,
) -> ExportedReportRows:
    job_request = DeviceManagementExportJob(
        report_name=report_name,
        select=select,
        filter=report_filter,
        format=DeviceManagementReportFileFormat.Csv,
    )
    logger.info("Starting Intune report export for %s", report_name)
    created_job = await client.device_management.reports.export_jobs.post(job_request)
    if not created_job or not created_job.id:
        raise ValueError(f"Export job creation for {report_name} returned no job id.")

    logger.info(
        "Created Intune report export job %s for %s",
        created_job.id,
        report_name,
    )
    completed_job = await wait_for_export_job(
        client,
        created_job.id,
        report_name,
        poll_interval_seconds=poll_interval_seconds,
        timeout_seconds=timeout_seconds,
    )
    if not completed_job.url:
        raise ValueError(
            f"Export job {created_job.id} for {report_name} completed without a URL."
        )

    report_data = download_export_report_rows(completed_job.url, report_name)
    logger.info(
        "Downloaded %d rows for Intune report %s from job %s",
        len(report_data.rows),
        report_name,
        created_job.id,
    )
    return report_data


@timeit
async def wait_for_export_job(
    client: GraphServiceClient,
    export_job_id: str,
    report_name: str,
    *,
    poll_interval_seconds: int = DEFAULT_REPORT_POLL_INTERVAL_SECONDS,
    timeout_seconds: int = DEFAULT_REPORT_TIMEOUT_SECONDS,
) -> DeviceManagementExportJob:
    started_at = time.monotonic()
    last_status: DeviceManagementReportStatus | None = None

    while True:
        job = await client.device_management.reports.export_jobs.by_device_management_export_job_id(
            export_job_id,
        ).get()
        if not job:
            raise ValueError(
                f"Export job {export_job_id} for {report_name} could not be fetched."
            )

        if job.status != last_status:
            logger.info(
                "Intune report export %s for %s is %s after %.1fs",
                export_job_id,
                report_name,
                _report_status_name(job.status),
                time.monotonic() - started_at,
            )
            last_status = job.status

        if job.status == DeviceManagementReportStatus.Completed:
            return job
        if job.status == DeviceManagementReportStatus.Failed:
            raise RuntimeError(f"Export job {export_job_id} for {report_name} failed.")
        if time.monotonic() - started_at > timeout_seconds:
            raise TimeoutError(
                f"Timed out waiting for export job {export_job_id} for {report_name} "
                f"after {timeout_seconds} seconds."
            )

        await asyncio.sleep(poll_interval_seconds)


def download_export_report_rows(
    download_url: str,
    report_name: str,
) -> ExportedReportRows:
    with (
        _build_retryable_session() as session,
        session.get(
            download_url,
            stream=True,
            timeout=EXPORT_DOWNLOAD_TIMEOUT_SECONDS,
        ) as response,
    ):
        response.raise_for_status()

        with tempfile.SpooledTemporaryFile(
            max_size=MAX_REPORT_ARCHIVE_BYTES,
        ) as archive_file:
            archive_size = 0
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                archive_size += len(chunk)
                if archive_size > MAX_REPORT_ARCHIVE_BYTES:
                    raise ValueError(
                        f"Export for {report_name} exceeded the maximum compressed size."
                    )
                archive_file.write(chunk)

            archive_file.seek(0)
            try:
                with zipfile.ZipFile(archive_file) as archive:
                    csv_members = [
                        info
                        for info in archive.infolist()
                        if info.filename.lower().endswith(".csv")
                    ]
                    if len(csv_members) != 1:
                        raise ValueError(
                            f"Export for {report_name} must contain exactly one CSV file."
                        )

                    csv_member = csv_members[0]
                    if csv_member.file_size > MAX_REPORT_UNCOMPRESSED_BYTES:
                        raise ValueError(
                            f"Export for {report_name} exceeded the maximum CSV size."
                        )

                    with archive.open(csv_member) as report_file:
                        decoded = io.TextIOWrapper(
                            report_file, encoding="utf-8-sig", newline=""
                        )
                        reader = csv.DictReader(decoded)
                        if not reader.fieldnames:
                            raise ValueError(
                                f"Export for {report_name} did not contain CSV headers."
                            )
                        rows = [
                            {
                                key: value if value != "" else None
                                for key, value in row.items()
                                if key is not None
                            }
                            for row in reader
                        ]
            except zipfile.BadZipFile as e:
                raise ValueError(
                    f"Export for {report_name} did not contain a valid zip archive."
                ) from e

    return ExportedReportRows(fieldnames=tuple(reader.fieldnames), rows=rows)


def _report_status_name(status: DeviceManagementReportStatus | None) -> str:
    if status is None:
        return "unknown"
    return str(status.value)


def _build_retryable_session() -> requests.Session:
    retry = Retry(
        total=EXPORT_DOWNLOAD_MAX_RETRIES,
        connect=EXPORT_DOWNLOAD_MAX_RETRIES,
        read=EXPORT_DOWNLOAD_MAX_RETRIES,
        backoff_factor=EXPORT_DOWNLOAD_RETRY_BACKOFF_SECONDS,
        status_forcelist=EXPORT_DOWNLOAD_RETRY_STATUS_CODES,
        allowed_methods=frozenset({"GET"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
