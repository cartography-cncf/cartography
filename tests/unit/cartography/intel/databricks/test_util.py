from datetime import timezone
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from threading import Thread

from cartography.intel.databricks.util import DatabricksWorkspaceClient
from cartography.intel.databricks.util import iso_to_datetime
from cartography.intel.databricks.util import parse_storage_url


class _RateLimitThenSuccessHandler(BaseHTTPRequestHandler):
    attempts = 0

    def do_GET(self) -> None:
        type(self).attempts += 1
        if self.attempts == 1:
            self.send_response(429)
            self.send_header("Retry-After", "1")
            self.end_headers()
            return

        body = b'{"ok": true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass


def test_client_configures_transient_retries():
    # Arrange
    client = DatabricksWorkspaceClient(
        "https://example.cloud.databricks.com",
        token="test-token",
    )

    # Act
    retry_policy = client._session.adapters["https://"].max_retries

    # Assert
    assert retry_policy.total == 5
    assert retry_policy.backoff_factor == 1
    assert retry_policy.status_forcelist == (429, 500, 502, 503, 504)
    assert retry_policy.allowed_methods == frozenset({"GET", "POST"})
    assert retry_policy.respect_retry_after_header is True


def test_client_retries_rate_limited_get_and_honors_retry_after(mocker):
    # Arrange
    _RateLimitThenSuccessHandler.attempts = 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), _RateLimitThenSuccessHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    client = DatabricksWorkspaceClient(
        f"http://127.0.0.1:{server.server_port}",
        token="test-token",
    )
    client._session.mount("http://", client._session.adapters["https://"])
    sleep = mocker.patch("urllib3.util.retry.time.sleep")

    try:
        # Act
        result = client.get("/test")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    # Assert
    assert result == {"ok": True}
    assert _RateLimitThenSuccessHandler.attempts == 2
    sleep.assert_called_once_with(1)


def test_iso_to_datetime():
    # Trailing Z (RFC-3339) and explicit offsets both parse to aware datetimes.
    dt = iso_to_datetime("2026-07-01T23:27:40Z")
    assert dt is not None
    assert dt.tzinfo is not None
    assert dt.astimezone(timezone.utc).hour == 23
    # Fractional seconds (Lakeview) parse too.
    assert iso_to_datetime("2026-07-01T23:29:14.783Z") is not None
    # Empty / missing values are dropped.
    assert iso_to_datetime(None) is None
    assert iso_to_datetime("") is None


def test_parse_storage_url():
    assert parse_storage_url("s3://my-bucket/uc/path") == ("s3", "my-bucket")
    assert parse_storage_url("gs://my-bucket/path") == ("gs", "my-bucket")
    assert parse_storage_url("abfss://container@acct.dfs.core.windows.net/path") == (
        "abfss",
        "container",
    )
    assert parse_storage_url(None) == (None, None)
    assert parse_storage_url("") == (None, None)
    assert parse_storage_url("not-a-url") == (None, None)
