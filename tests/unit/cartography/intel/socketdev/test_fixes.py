from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from threading import Thread
from unittest.mock import call
from unittest.mock import MagicMock

import pytest
import requests

import cartography.intel.socketdev.fixes as fixes


class _UnavailableThenSuccessHandler(BaseHTTPRequestHandler):
    attempts = 0

    def do_GET(self) -> None:
        type(self).attempts += 1
        if self.attempts == 1:
            self.send_response(503)
            self.end_headers()
            return

        body = b'{"fixDetails": {}}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass


class _RateLimitedHandler(BaseHTTPRequestHandler):
    attempts = 0

    def do_GET(self) -> None:
        type(self).attempts += 1
        self.send_response(429)
        self.send_header("Retry-After", "3600")
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        pass


def test_get_retries_transient_failure(mocker):
    _UnavailableThenSuccessHandler.attempts = 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), _UnavailableThenSuccessHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    session = fixes._create_session("test-token")
    session.mount("http://", session.adapters["https://"])
    mocker.patch.object(fixes, "_BASE_URL", f"http://127.0.0.1:{server.server_port}")

    try:
        result = fixes.get(session, "example-org", "example-repo", "CVE-2026-0001")
    finally:
        session.close()
        server.shutdown()
        server.server_close()
        thread.join()

    assert result == {"fixDetails": {}}
    assert _UnavailableThenSuccessHandler.attempts == 2


def test_get_bounds_rate_limit_retry_delay(mocker):
    _RateLimitedHandler.attempts = 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), _RateLimitedHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    session = fixes._create_session("test-token")
    session.mount("http://", session.adapters["https://"])
    mocker.patch.object(fixes, "_BASE_URL", f"http://127.0.0.1:{server.server_port}")
    sleep = mocker.patch("urllib3.util.retry.time.sleep")

    try:
        with pytest.raises(requests.RequestException):
            fixes.get(session, "example-org", "example-repo", "CVE-2026-0001")
    finally:
        session.close()
        server.shutdown()
        server.server_close()
        thread.join()

    assert _RateLimitedHandler.attempts == 4
    assert sleep.call_args_list == [call(8), call(8), call(8)]


def test_sync_fixes_matches_alert_by_full_package_identity(mocker):
    api_session = MagicMock()
    api_session.__enter__.return_value = api_session
    mocker.patch.object(fixes, "_create_session", return_value=api_session)
    mocker.patch.object(
        fixes,
        "get",
        return_value={
            "fixDetails": {
                "GHSA-example": {
                    "type": "fixFound",
                    "value": {
                        "fixDetails": {
                            "fixes": [
                                {
                                    "purl": "pkg:npm/%40scope/package-b@2.0.0",
                                    "fixedVersion": "2.0.1",
                                },
                                {
                                    "purl": "pkg:pypi/package-b@2.0.0",
                                    "fixedVersion": "2.0.1",
                                },
                            ],
                        },
                    },
                },
            },
        },
    )
    load_fixes = mocker.patch.object(fixes, "load_fixes")
    mocker.patch.object(fixes, "cleanup")

    fixes.sync_fixes(
        MagicMock(),
        "test-token",
        "example-repo",
        1,
        {"UPDATE_TAG": 1, "ORG_ID": "example-org"},
        [
            {
                "id": "alert-scoped-npm",
                "repo_slug": "example-repo",
                "ghsa_id": "GHSA-example",
                "artifact_type": "npm",
                "artifact_namespace": "@scope",
                "artifact_name": "package-b",
                "artifact_version": "2.0.0",
            },
            {
                "id": "alert-pypi",
                "repo_slug": "example-repo",
                "ghsa_id": "GHSA-example",
                "artifact_type": "pypi",
                "artifact_name": "package-b",
                "artifact_version": "2.0.0",
            },
            {
                "id": "alert-unscoped-npm",
                "repo_slug": "example-repo",
                "ghsa_id": "GHSA-example",
                "artifact_type": "npm",
                "artifact_namespace": None,
                "artifact_name": "package-b",
                "artifact_version": "2.0.0",
            },
        ],
        [],
    )

    loaded_fixes = {
        fix["purl"]: fix["alert_id"] for fix in load_fixes.call_args.args[1]
    }
    assert loaded_fixes == {
        "pkg:npm/%40scope/package-b@2.0.0": "alert-scoped-npm",
        "pkg:pypi/package-b@2.0.0": "alert-pypi",
    }


def test_sync_fixes_batches_vulnerability_ids(mocker):
    api_session = MagicMock()
    api_session.__enter__.return_value = api_session
    mocker.patch.object(fixes, "_create_session", return_value=api_session)
    get = mocker.patch.object(fixes, "get", return_value={"fixDetails": {}})
    cleanup = mocker.patch.object(fixes, "cleanup")
    alerts = [
        {
            "id": f"alert-{index}",
            "repo_slug": "example-repo",
            "cve_id": f"CVE-2026-{index:04d}",
        }
        for index in range(201)
    ]

    fixes.sync_fixes(
        MagicMock(),
        "test-token",
        "example-org",
        1,
        {"UPDATE_TAG": 1, "ORG_ID": "example-org"},
        alerts,
        [],
    )

    batches = [call.args[3].split(",") for call in get.call_args_list]
    assert [len(batch) for batch in batches] == [
        100,
        100,
        1,
    ]
    assert [item for batch in batches for item in batch] == sorted(
        alert["cve_id"] for alert in alerts
    )
    assert all(call.args[0] is api_session for call in get.call_args_list)
    cleanup.assert_called_once()


def test_sync_fixes_skips_load_and_cleanup_when_a_batch_fails(mocker):
    api_session = MagicMock()
    api_session.__enter__.return_value = api_session
    mocker.patch.object(fixes, "_create_session", return_value=api_session)
    get = mocker.patch.object(
        fixes,
        "get",
        side_effect=[{"fixDetails": {}}, requests.RequestException("failed")],
    )
    load_fixes = mocker.patch.object(fixes, "load_fixes")
    cleanup = mocker.patch.object(fixes, "cleanup")
    alerts = [
        {
            "id": f"alert-{index}",
            "repo_slug": "example-repo",
            "cve_id": f"CVE-2026-{index:04d}",
        }
        for index in range(101)
    ]

    with pytest.raises(requests.RequestException):
        fixes.sync_fixes(
            MagicMock(),
            "test-token",
            "example-org",
            1,
            {"UPDATE_TAG": 1, "ORG_ID": "example-org"},
            alerts,
            [],
        )

    assert get.call_count == 2
    load_fixes.assert_not_called()
    cleanup.assert_not_called()
