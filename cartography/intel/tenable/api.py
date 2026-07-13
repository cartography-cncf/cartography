import logging
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

_EXPORT_POLL_INTERVAL = 30  # seconds between status polls
_MAX_POLL_ATTEMPTS = 60  # 30 minutes maximum wait

_RETRY_POLICY = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)


def get_tenable_session(access_key: str, secret_key: str) -> requests.Session:
    """
    Build an authenticated requests.Session for the Tenable API.
    Authentication uses the X-ApiKeys header as documented at
    https://developer.tenable.com/docs/authorization.

    GET requests are retried up to 5 times with exponential backoff on
    transient errors (429, 500, 502, 503, 504).
    """
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=_RETRY_POLICY))
    session.headers.update(
        {
            "X-ApiKeys": f"accessKey={access_key};secretKey={secret_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    )
    return session


def _initiate_export(
    session: requests.Session,
    base_url: str,
    export_path: str,
    params: dict[str, Any],
) -> str:
    """POST to start an async export job. Returns the export UUID."""
    url = f"{base_url}/{export_path}"
    response = session.post(url, json=params, timeout=(30, 30))
    response.raise_for_status()
    return response.json()["export_uuid"]


def _get_export_status(
    session: requests.Session,
    base_url: str,
    result_base: str,
    export_uuid: str,
) -> dict[str, Any]:
    """GET the current status of an async export job."""
    url = f"{base_url}/{result_base}/{export_uuid}/status"
    response = session.get(url, timeout=(30, 30))
    response.raise_for_status()
    return response.json()


def _download_chunk(
    session: requests.Session,
    base_url: str,
    result_base: str,
    export_uuid: str,
    chunk_id: int,
) -> list[dict[str, Any]]:
    """GET a single chunk of exported data."""
    url = f"{base_url}/{result_base}/{export_uuid}/chunks/{chunk_id}"
    response = session.get(url, timeout=(30, 120))
    response.raise_for_status()
    return response.json()


def export_and_download(
    session: requests.Session,
    base_url: str,
    export_path: str,
    result_base: str,
    export_params: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Run the full Tenable async export workflow:
    1. POST to initiate the export job
    2. Poll the status endpoint until status is FINISHED
    3. Download and concatenate all available chunks

    :param session: Authenticated requests.Session
    :param base_url: Tenable base URL, e.g. "https://cloud.tenable.com"
    :param export_path: Path to POST for initiating the export,
        e.g. "assets/v2/export" or "vulns/export"
    :param result_base: Base path for status and chunk endpoints,
        e.g. "assets/export" or "vulns/export"
    :param export_params: Body parameters for the export POST request
    :return: Aggregated list of all exported records
    """
    export_uuid = _initiate_export(session, base_url, export_path, export_params)
    logger.info("Initiated Tenable export %s (endpoint: %s)", export_uuid, export_path)

    for attempt in range(1, _MAX_POLL_ATTEMPTS + 1):
        status_data = _get_export_status(session, base_url, result_base, export_uuid)
        status = status_data.get("status")

        if status == "ERROR":
            raise RuntimeError(f"Tenable export {export_uuid} failed with status ERROR")
        if status == "CANCELLED":
            raise RuntimeError(f"Tenable export {export_uuid} was cancelled")
        if status == "FINISHED":
            chunks = status_data.get("chunks_available") or []
            logger.info(
                "Tenable export %s finished; downloading %d chunk(s)",
                export_uuid,
                len(chunks),
            )
            results: list[dict[str, Any]] = []
            for chunk_id in chunks:
                chunk_data = _download_chunk(
                    session, base_url, result_base, export_uuid, chunk_id
                )
                logger.debug(
                    "Downloaded chunk %s (%d records)", chunk_id, len(chunk_data)
                )
                results.extend(chunk_data)
            return results

        logger.info(
            "Tenable export %s status: %s (attempt %d/%d) — waiting %ds",
            export_uuid,
            status,
            attempt,
            _MAX_POLL_ATTEMPTS,
            _EXPORT_POLL_INTERVAL,
        )
        time.sleep(_EXPORT_POLL_INTERVAL)

    raise TimeoutError(
        f"Tenable export {export_uuid} did not finish after "
        f"{_MAX_POLL_ATTEMPTS} polls ({_MAX_POLL_ATTEMPTS * _EXPORT_POLL_INTERVAL}s)"
    )
