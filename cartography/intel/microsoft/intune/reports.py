import asyncio
import csv
import io
import logging
import tempfile
import time
import zipfile
from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import dataclass
from dataclasses import field
from types import TracebackType
from typing import IO

import requests
from kiota_abstractions.api_error import APIError
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
DEFAULT_EXPORT_JOB_MAX_ATTEMPTS = 3
EXPORT_DOWNLOAD_TIMEOUT_SECONDS = 60
# Exports are spooled to disk and parsed as a stream, so these caps only guard
# against a runaway download. AppInvRawData is one row per (device, app) pair
# and reaches hundreds of MB compressed for tenants with tens of thousands of
# managed devices.
MAX_REPORT_ARCHIVE_BYTES = 2 * 1024 * 1024 * 1024
MAX_REPORT_UNCOMPRESSED_BYTES = 16 * 1024 * 1024 * 1024
EXPORT_DOWNLOAD_MAX_RETRIES = 3
EXPORT_DOWNLOAD_RETRY_BACKOFF_SECONDS = 1.0
TRANSIENT_STATUS_CODES = (429, 500, 502, 503, 504)


class IntuneReportExportError(Exception):
    """Raised when an Intune report export cannot produce rows.

    Scoped to the export-job boundary (job submission, polling, download) so
    callers can tolerate a failed export without masking unrelated errors from
    later report-processing phases.
    """


class IntuneReportTooLargeError(IntuneReportExportError):
    """Raised when an export exceeds the download or CSV size cap."""


class _ArchivedCsvRows:
    """Re-iterable CSV rows read lazily from a zip archive on disk.

    Large exports do not fit in memory as materialized dicts, and the detected
    apps sync needs two passes over AppInvRawData (nodes before relationships),
    so each iteration re-opens the CSV member and streams it again.
    """

    def __init__(self, archive_file: IO[bytes], member: zipfile.ZipInfo) -> None:
        self._archive_file = archive_file
        self._member = member

    def __iter__(self) -> Iterator[dict[str, str | None]]:
        self._archive_file.seek(0)
        with (
            zipfile.ZipFile(self._archive_file) as archive,
            archive.open(self._member) as report_file,
        ):
            reader = csv.DictReader(
                io.TextIOWrapper(report_file, encoding="utf-8-sig", newline=""),
            )
            for row in reader:
                yield {
                    key: value if value != "" else None
                    for key, value in row.items()
                    if key is not None
                }


@dataclass(frozen=True)
class ExportedReportRows:
    fieldnames: tuple[str, ...]
    rows: Iterable[dict[str, str | None]]
    archive_file: IO[bytes] | None = field(default=None, repr=False)

    def close(self) -> None:
        if self.archive_file is not None:
            self.archive_file.close()

    def __enter__(self) -> "ExportedReportRows":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


@timeit
async def export_report_rows(
    client: GraphServiceClient,
    report_name: str,
    select: list[str],
    *,
    report_filter: str | None = None,
    poll_interval_seconds: int = DEFAULT_REPORT_POLL_INTERVAL_SECONDS,
    timeout_seconds: int = DEFAULT_REPORT_TIMEOUT_SECONDS,
    max_attempts: int = DEFAULT_EXPORT_JOB_MAX_ATTEMPTS,
) -> ExportedReportRows:
    job_request = DeviceManagementExportJob(
        report_name=report_name,
        select=select,
        filter=report_filter,
        format=DeviceManagementReportFileFormat.Csv,
    )

    last_export_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        logger.info(
            "Starting Intune report export for %s (attempt %d/%d)",
            report_name,
            attempt,
            max_attempts,
        )
        created_job = await client.device_management.reports.export_jobs.post(
            job_request,
        )
        if not created_job or not created_job.id:
            raise ValueError(
                f"Export job creation for {report_name} returned no job id."
            )

        logger.info(
            "Created Intune report export job %s for %s",
            created_job.id,
            report_name,
        )
        try:
            completed_job = await wait_for_export_job(
                client,
                created_job.id,
                report_name,
                poll_interval_seconds=poll_interval_seconds,
                timeout_seconds=timeout_seconds,
            )
            if not completed_job.url:
                raise RuntimeError(
                    f"Export job {created_job.id} for {report_name} completed "
                    "without a URL."
                )
            report_data = download_export_report_rows(completed_job.url, report_name)
        except (TimeoutError, RuntimeError, requests.RequestException) as e:
            # Microsoft Graph intermittently strands an export job in
            # `inProgress`, marks it `failed`, marks it `completed` with no
            # download URL, or hands back a URL whose blob does not exist,
            # even for tiny tenants whose report normally completes in
            # seconds. The bad job never recovers, but resubmitting yields a
            # fresh job that almost always succeeds, so retry instead of
            # failing the sync.
            last_export_error = e
            logger.warning(
                "Intune report export job %s for %s did not complete on "
                "attempt %d/%d: %s",
                created_job.id,
                report_name,
                attempt,
                max_attempts,
                e,
            )
            continue

        logger.info(
            "Downloaded Intune report %s from job %s",
            report_name,
            created_job.id,
        )
        return report_data

    raise IntuneReportExportError(
        f"Intune report export for {report_name} did not complete after "
        f"{max_attempts} attempt(s)."
    ) from last_export_error


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
        try:
            job = await client.device_management.reports.export_jobs.by_device_management_export_job_id(
                export_job_id,
            ).get()
        except APIError as e:
            # Graph answers a poll with 5xx or 429 now and then while the job
            # itself keeps running, so a failed poll is not a failed job. The
            # timeout below still bounds a job that never answers.
            if e.response_status_code not in TRANSIENT_STATUS_CODES:
                raise
            logger.warning(
                "Polling Intune report export %s for %s failed with %s; "
                "polling again.",
                export_job_id,
                report_name,
                e.response_status_code,
            )
        else:
            if not job:
                raise ValueError(
                    f"Export job {export_job_id} for {report_name} could not be "
                    "fetched."
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
                raise RuntimeError(
                    f"Export job {export_job_id} for {report_name} failed."
                )
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
    """Download an export to a temp file; the caller must close the result."""
    archive_file = tempfile.TemporaryFile()
    try:
        _download_archive(download_url, report_name, archive_file)
        fieldnames, csv_member = _read_csv_header(archive_file, report_name)
    except BaseException:
        archive_file.close()
        raise
    return ExportedReportRows(
        fieldnames=fieldnames,
        rows=_ArchivedCsvRows(archive_file, csv_member),
        archive_file=archive_file,
    )


def _download_archive(
    download_url: str,
    report_name: str,
    archive_file: IO[bytes],
) -> None:
    with (
        _build_retryable_session() as session,
        session.get(
            download_url,
            stream=True,
            timeout=EXPORT_DOWNLOAD_TIMEOUT_SECONDS,
        ) as response,
    ):
        response.raise_for_status()
        archive_size = 0
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if not chunk:
                continue
            archive_size += len(chunk)
            if archive_size > MAX_REPORT_ARCHIVE_BYTES:
                raise IntuneReportTooLargeError(
                    f"Export for {report_name} exceeded the maximum compressed "
                    f"size of {MAX_REPORT_ARCHIVE_BYTES} bytes."
                )
            archive_file.write(chunk)


def _read_csv_header(
    archive_file: IO[bytes],
    report_name: str,
) -> tuple[tuple[str, ...], zipfile.ZipInfo]:
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
                raise IntuneReportTooLargeError(
                    f"Export for {report_name} exceeded the maximum CSV size "
                    f"of {MAX_REPORT_UNCOMPRESSED_BYTES} bytes."
                )

            with archive.open(csv_member) as report_file:
                reader = csv.DictReader(
                    io.TextIOWrapper(report_file, encoding="utf-8-sig", newline=""),
                )
                if not reader.fieldnames:
                    raise ValueError(
                        f"Export for {report_name} did not contain CSV headers."
                    )
                return tuple(reader.fieldnames), csv_member
    except zipfile.BadZipFile as e:
        raise ValueError(
            f"Export for {report_name} did not contain a valid zip archive."
        ) from e


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
        status_forcelist=TRANSIENT_STATUS_CODES,
        allowed_methods=frozenset({"GET"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
