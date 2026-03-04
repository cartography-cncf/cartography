import csv
import io
import json
import logging
import time
import zipfile
from typing import Any
from typing import IO
from typing import Iterator
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)


class SantaEventExportEndpointUnavailable(RuntimeError):
    """Raised when Zentral does not expose the Santa events export endpoint."""


class ZentralSantaClient:
    """Client for Zentral machine snapshot and Santa event export APIs."""

    MACHINE_SNAPSHOTS_EXPORT_ENDPOINT = "/api/inventory/machines/export_snapshots/"
    SANTA_EVENTS_EXPORT_ENDPOINT = "/api/santa/events/export/"

    def __init__(
        self,
        base_url: str,
        token: str,
        request_timeout: int = 60,
        poll_interval_seconds: float = 1.0,
        max_poll_seconds: int = 600,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = (request_timeout, request_timeout)
        self._poll_interval_seconds = poll_interval_seconds
        self._max_poll_seconds = max_poll_seconds

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/json",
                "Authorization": f"Token {token}",
            },
        )

    def export_machine_snapshots(self, source_name: str) -> Iterator[dict[str, Any]]:
        params: dict[str, str] = {}
        if source_name:
            params["source_name"] = source_name
        task_result_url = self._start_export(
            self.MACHINE_SNAPSHOTS_EXPORT_ENDPOINT,
            params=params or None,
        )
        yield from self._iter_task_records(task_result_url)

    def export_santa_events(self, source_name: str) -> Iterator[dict[str, Any]]:
        params: dict[str, str] = {"export_format": "zip"}
        if source_name:
            params["source_name"] = source_name
        task_result_url = self._start_export(
            self.SANTA_EVENTS_EXPORT_ENDPOINT,
            params=params,
        )
        yield from self._iter_task_records(task_result_url)

    def _start_export(
        self,
        endpoint: str,
        params: dict[str, str] | None = None,
    ) -> str:
        response = self._session.post(
            self._absolute_url(endpoint),
            params=params,
            timeout=self._timeout,
        )

        if endpoint == self.SANTA_EVENTS_EXPORT_ENDPOINT and response.status_code in {
            404,
            405,
        }:
            raise SantaEventExportEndpointUnavailable(
                "Zentral Santa event export endpoint is unavailable (404/405). "
                "Santa app-on-machine mapping requires /api/santa/events/export/."
            )

        response.raise_for_status()
        payload = response.json()
        task_result_url = payload.get("task_result_url")
        if not task_result_url:
            raise RuntimeError(
                f"Zentral export endpoint {endpoint} did not return task_result_url",
            )
        return str(task_result_url)

    def _iter_task_records(self, task_result_url: str) -> Iterator[dict[str, Any]]:
        download_url = self._wait_for_task(task_result_url)
        response = self._session.get(download_url, timeout=self._timeout)
        response.raise_for_status()
        yield from self._iter_records_from_blob(response.content)

    def _wait_for_task(self, task_result_url: str) -> str:
        started = time.monotonic()
        url = self._absolute_url(task_result_url)

        while True:
            response = self._session.get(url, timeout=self._timeout)
            response.raise_for_status()
            payload = response.json()

            if payload.get("unready"):
                if time.monotonic() - started > self._max_poll_seconds:
                    raise TimeoutError(
                        f"Timed out waiting for Zentral task result at {task_result_url}",
                    )
                time.sleep(self._poll_interval_seconds)
                continue

            status = payload.get("status")
            if status != "SUCCESS":
                raise RuntimeError(
                    f"Zentral task {payload.get('id')} completed with status '{status}'",
                )

            download_url = payload.get("download_url")
            if not download_url:
                raise RuntimeError(
                    f"Zentral task {payload.get('id')} did not include download_url",
                )
            return self._absolute_url(str(download_url))

    def _iter_records_from_blob(self, blob: bytes) -> Iterator[dict[str, Any]]:
        if self._is_zip_blob(blob):
            yield from self._iter_records_from_zip(blob)
            return

        yield from self._iter_records_from_text_blob(blob)

    def _iter_records_from_zip(self, blob: bytes) -> Iterator[dict[str, Any]]:
        with zipfile.ZipFile(io.BytesIO(blob), mode="r") as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                filename = info.filename.lower()
                with archive.open(info, mode="r") as data:
                    if filename.endswith(".jsonl"):
                        yield from self._iter_jsonl_records(data)
                    elif filename.endswith(".csv"):
                        yield from self._iter_csv_records(data)

    def _iter_records_from_text_blob(self, blob: bytes) -> Iterator[dict[str, Any]]:
        payload = blob.lstrip()
        if not payload:
            return

        if payload.startswith(b"["):
            parsed = json.loads(payload.decode("utf-8"))
            if isinstance(parsed, list):
                for row in parsed:
                    if isinstance(row, dict):
                        yield row
            return

        if payload.startswith(b"{"):
            yield from self._iter_jsonl_records(io.BytesIO(blob))
            return

        yield from self._iter_csv_records(io.BytesIO(blob))

    @staticmethod
    def _iter_jsonl_records(stream: IO[bytes]) -> Iterator[dict[str, Any]]:
        text = stream.read().decode("utf-8")
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                yield parsed

    @staticmethod
    def _iter_csv_records(stream: IO[bytes]) -> Iterator[dict[str, Any]]:
        text = stream.read().decode("utf-8")
        sample = text[:2048]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel

        for row in csv.DictReader(io.StringIO(text), dialect=dialect):
            if any(value not in (None, "") for value in row.values()):
                yield row

    @staticmethod
    def _is_zip_blob(blob: bytes) -> bool:
        if not blob:
            return False
        return zipfile.is_zipfile(io.BytesIO(blob))

    def _absolute_url(self, path: str) -> str:
        return urljoin(f"{self._base_url}/", path.lstrip("/"))
