import json
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from threading import Thread

import pytest
import requests

import cartography.intel.socketdev.dependencies as dependencies
import cartography.intel.socketdev.util as socketdev_util

_PAGES = {
    0: {"rows": [{"id": "dep-1"}, {"id": "dep-2"}], "end": False},
    2: {"rows": [{"id": "dep-3"}], "end": True},
}


class _SecondPageFailsHandler(BaseHTTPRequestHandler):
    failure_status = 500
    failures_left = 0
    attempts_by_offset: dict[int, int] = {}

    def do_POST(self) -> None:
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        offset = body["offset"]
        cls = type(self)
        cls.attempts_by_offset[offset] = cls.attempts_by_offset.get(offset, 0) + 1
        if offset > 0 and cls.failures_left > 0:
            cls.failures_left -= 1
            self.send_response(cls.failure_status)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        payload = json.dumps(_PAGES[offset]).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture
def socket_api(mocker):
    server = ThreadingHTTPServer(("127.0.0.1", 0), _SecondPageFailsHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    create_session = socketdev_util._create_session

    def create_plain_http_session(api_token: str) -> requests.Session:
        session = create_session(api_token)
        session.mount("http://", session.adapters["https://"])
        return session

    mocker.patch.object(
        dependencies,
        "_create_session",
        side_effect=create_plain_http_session,
    )
    mocker.patch.object(
        dependencies,
        "_BASE_URL",
        f"http://127.0.0.1:{server.server_port}",
    )
    mocker.patch("urllib3.util.retry.time.sleep")
    _SecondPageFailsHandler.attempts_by_offset = {}

    yield _SecondPageFailsHandler

    server.shutdown()
    server.server_close()
    thread.join()


@pytest.mark.parametrize("failure_status", [429, 500, 502, 503, 504])
def test_get_retries_transient_page_failure(socket_api, failure_status):
    socket_api.failure_status = failure_status
    socket_api.failures_left = 1

    result = dependencies.get("test-token")

    assert result == [{"id": "dep-1"}, {"id": "dep-2"}, {"id": "dep-3"}]
    assert socket_api.attempts_by_offset == {0: 1, 2: 2}


def test_get_raises_when_page_keeps_failing(socket_api):
    socket_api.failure_status = 500
    socket_api.failures_left = 10

    with pytest.raises(requests.HTTPError, match="500 Server Error"):
        dependencies.get("test-token")

    assert socket_api.attempts_by_offset == {0: 1, 2: 4}
