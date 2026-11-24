import json
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from threading import Thread
from typing import Any

import pytest
import requests

import cartography.intel.socketdev.dependencies as dependencies
import cartography.intel.socketdev.util as socketdev_util


class _ScriptedSocketApi(BaseHTTPRequestHandler):
    """Answers each dependency search with the next scripted (status, body)."""

    script: list[tuple[int, dict[str, Any]]] = []

    def do_POST(self) -> None:
        self.rfile.read(int(self.headers["Content-Length"]))
        status, body = type(self).script.pop(0)
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture
def socket_api(mocker):
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ScriptedSocketApi)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    create_session = socketdev_util._create_session

    # The module's session retries only over https, and the local server is http.
    def create_session_for_local_server(api_token: str) -> requests.Session:
        session = create_session(api_token)
        session.mount("http://", session.adapters["https://"])
        return session

    mocker.patch.object(
        dependencies,
        "_create_session",
        side_effect=create_session_for_local_server,
    )
    mocker.patch.object(
        dependencies,
        "_BASE_URL",
        f"http://127.0.0.1:{server.server_port}",
    )
    mocker.patch("urllib3.util.retry.time.sleep")

    yield _ScriptedSocketApi

    server.shutdown()
    server.server_close()
    thread.join()


@pytest.mark.parametrize("transient_status", [429, 500, 503])
def test_get_returns_every_page_when_a_page_fails_once(socket_api, transient_status):
    socket_api.script = [
        (200, {"rows": [{"id": "dep-1"}, {"id": "dep-2"}], "end": False}),
        (transient_status, {}),
        (200, {"rows": [{"id": "dep-3"}], "end": True}),
    ]

    result = dependencies.get("test-token")

    assert result == [{"id": "dep-1"}, {"id": "dep-2"}, {"id": "dep-3"}]


def test_get_raises_when_a_page_keeps_failing(socket_api):
    socket_api.script = [
        (200, {"rows": [{"id": "dep-1"}], "end": False}),
        *[(500, {})] * 10,
    ]

    with pytest.raises(requests.HTTPError, match="500 Server Error"):
        dependencies.get("test-token")
