import json
from io import BytesIO
from typing import Any
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests
from urllib3.connectionpool import HTTPSConnectionPool
from urllib3.response import HTTPResponse

from cartography.cli import CLI
from cartography.config import Config
from cartography.intel.zoom import start_zoom_ingestion
from cartography.intel.zoom.client import TOKEN_URL
from cartography.intel.zoom.client import USERS_URL
from cartography.intel.zoom.client import ZoomClient


def response(status: int, payload: dict[str, Any]) -> requests.Response:
    result = requests.Response()
    result.status_code = status
    result._content = json.dumps(payload).encode()
    return result


def test_client_refreshes_expired_token_and_one_401() -> None:
    # Arrange
    client = ZoomClient("account-a", "client-id", "secret")
    post = MagicMock(
        side_effect=[
            response(200, {"access_token": token, "expires_in": 3600})
            for token in ("first", "second", "third")
        ]
    )
    get = MagicMock(
        side_effect=[
            response(401, {}),
            response(200, {"users": []}),
            response(200, {"users": []}),
        ]
    )

    # Act
    with (
        client.session,
        patch.object(client.session, "post", post),
        patch.object(client.session, "get", get),
        patch(
            "cartography.intel.zoom.client.time.monotonic",
            side_effect=[0, 0, 0, 3600, 3600],
        ),
    ):
        assert client.get_users_page({"status": "active"}) == {"users": []}
        assert client.get_users_page({"status": "inactive"}) == {"users": []}

    # Assert
    assert post.call_count == 3
    post.assert_called_with(
        TOKEN_URL,
        data={"grant_type": "account_credentials", "account_id": "account-a"},
        auth=("client-id", "secret"),
        timeout=(10, 60),
        allow_redirects=False,
    )
    assert [call.kwargs["headers"]["Authorization"] for call in get.call_args_list] == [
        "Bearer first",
        "Bearer second",
        "Bearer third",
    ]
    assert all(call.args[0] == USERS_URL for call in get.call_args_list)


def test_client_stops_after_repeated_401() -> None:
    # Arrange
    client = ZoomClient("account-a", "client-id", "secret")
    # Act and assert
    with (
        client.session,
        patch.object(
            client.session,
            "post",
            return_value=response(200, {"access_token": "token", "expires_in": 3600}),
        ),
        patch.object(client.session, "get", return_value=response(401, {})) as get,
        pytest.raises(requests.HTTPError),
    ):
        client.get_users_page({"status": "active"})
    assert get.call_count == 2


def wire_response(status: int, payload: dict[str, Any]) -> HTTPResponse:
    return HTTPResponse(
        status=status,
        body=BytesIO(json.dumps(payload).encode()),
        headers={"Retry-After": "3600"},
        preload_content=False,
    )


def test_client_retries_token_and_users_with_capped_delays() -> None:
    # Arrange
    client = ZoomClient("account-a", "client-id", "secret")
    responses = [
        wire_response(503, {}),
        wire_response(200, {"access_token": "token", "expires_in": 3600}),
        wire_response(429, {}),
        wire_response(200, {"users": [{"id": "user-1"}]}),
    ]

    # Act: replace only network I/O; requests and urllib3 run their real retries.
    with (
        client.session,
        patch.object(
            HTTPSConnectionPool, "_make_request", side_effect=responses
        ) as send,
        patch("urllib3.util.retry.time.sleep") as sleep,
    ):
        result = client.get_users_page({"status": "active"})

    # Assert
    assert result == {"users": [{"id": "user-1"}]}
    assert [request.args[1] for request in send.call_args_list] == [
        "POST",
        "POST",
        "GET",
        "GET",
    ]
    assert sleep.call_args_list == [call(8), call(8)]


@pytest.mark.parametrize("status, attempts", [(429, 4), (403, 1)])  # type: ignore[misc]
def test_client_stops_on_sustained_rate_limit_or_forbidden(
    status: int, attempts: int
) -> None:
    # Arrange
    client = ZoomClient("account-a", "client-id", "secret")
    responses = [
        wire_response(200, {"access_token": "token", "expires_in": 3600}),
        *(wire_response(status, {}) for _ in range(attempts)),
    ]

    # Act and assert
    with (
        client.session,
        patch.object(
            HTTPSConnectionPool, "_make_request", side_effect=responses
        ) as send,
        patch("urllib3.util.retry.time.sleep") as sleep,
        pytest.raises(requests.HTTPError) as error,
    ):
        client.get_users_page({"status": "active"})
    assert error.value.response.status_code == status
    assert send.call_count == attempts + 1
    assert sleep.call_args_list == [call(8)] * (attempts - 1)


@pytest.mark.parametrize("endpoint", ["token", "users"])  # type: ignore[misc]
def test_client_rejects_redirects_even_with_valid_json(endpoint: str) -> None:
    # Arrange
    client = ZoomClient("account-a", "client-id", "secret")
    # Act and assert
    with (
        client.session,
        patch.object(
            client.session,
            "post",
            return_value=response(
                302 if endpoint == "token" else 200,
                {"access_token": "token", "expires_in": 3600},
            ),
        ),
        patch.object(client.session, "get", return_value=response(302, {"users": []})),
        pytest.raises(requests.HTTPError),
    ):
        client.get_users_page({"status": "active"})


def test_cli_wires_account_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setenv("TEST_ZOOM_SECRET", "secret")
    cli = CLI(MagicMock(), "test")

    # Act
    with patch("cartography.sync.run_with_config", return_value=0) as run:
        code = cli.main(
            [
                "--neo4j-uri",
                "bolt://localhost:7687",
                "--selected-modules",
                "zoom",
                "--zoom-account-id",
                "account-a",
                "--zoom-client-id",
                "client-id",
                "--zoom-client-secret-env-var",
                "TEST_ZOOM_SECRET",
            ]
        )

    # Assert
    assert code == 0
    config = run.call_args[0][1]
    assert config.zoom_account_id == "account-a"
    assert config.zoom_client_id == "client-id"
    assert config.zoom_client_secret == "secret"


def test_unconfigured_module_does_not_request_credentials() -> None:
    # Arrange
    config = Config(neo4j_uri="bolt://localhost:7687")

    # Act
    with patch("cartography.intel.zoom.ZoomClient") as client:
        start_zoom_ingestion(MagicMock(), config)

    # Assert
    client.assert_not_called()
