from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from threading import Thread
from unittest.mock import call

import pytest
import requests
from pytest_mock import MockerFixture

from cartography.intel.jira.util import JiraClient
from tests.data.jira.access import CLOUD_ID


@pytest.fixture  # type: ignore[misc]
def local_api() -> Iterator[tuple[JiraClient, list[int], list[str]]]:
    statuses: list[int] = []
    paths: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            paths.append(self.path)
            status = statuses.pop(0)
            self.send_response(status)
            if status == 429:
                self.send_header("Retry-After", "3600")
            if status == 302:
                self.send_header(
                    "Location", f"http://localhost:{server.server_port}/redirected"
                )
            body = b'{"deploymentType": "Cloud"}'
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    client = JiraClient(CLOUD_ID, "reader@example.com", "test-token")
    client.base_url = f"http://127.0.0.1:{server.server_port}"
    client.session.mount("http://", client.session.adapters["https://"])
    try:
        with client.session:
            yield client, statuses, paths
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize("status", [429, 502, 503, 504])  # type: ignore[misc]
def test_transient_failure_retries_then_succeeds(
    local_api: tuple[JiraClient, list[int], list[str]],
    mocker: MockerFixture,
    status: int,
) -> None:
    # Arrange
    client, statuses, paths = local_api
    statuses.extend([status, 200])
    sleep = mocker.patch("urllib3.util.retry.time.sleep")
    # Act
    result = client.get("serverInfo")
    # Assert
    assert result == {"deploymentType": "Cloud"}
    assert paths == ["/rest/api/3/serverInfo"] * 2
    assert sleep.call_args_list == ([call(8)] if status == 429 else [])


def test_rate_limit_exhausts_retry_budget_with_bounded_delays(
    local_api: tuple[JiraClient, list[int], list[str]], mocker: MockerFixture
) -> None:
    # Arrange
    client, statuses, paths = local_api
    statuses.extend([429] * 4)
    sleep = mocker.patch("urllib3.util.retry.time.sleep")
    # Act and assert
    with pytest.raises(requests.exceptions.RetryError):
        client.get("serverInfo")
    assert paths == ["/rest/api/3/serverInfo"] * 4
    assert sleep.call_args_list == [call(8)] * 3


def test_redirect_is_rejected_before_following_another_origin(
    local_api: tuple[JiraClient, list[int], list[str]],
) -> None:
    # Arrange
    client, statuses, paths = local_api
    statuses.extend([302, 200])
    # Act and assert
    with pytest.raises(requests.HTTPError, match="unexpectedly redirected"):
        client.get("serverInfo")
    assert paths == ["/rest/api/3/serverInfo"]
