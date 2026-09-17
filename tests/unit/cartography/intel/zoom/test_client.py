from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from cartography.cli import CLI
from cartography.config import Config
from cartography.intel.zoom import start_zoom_ingestion
from cartography.intel.zoom.client import TOKEN_URL
from cartography.intel.zoom.client import USERS_URL
from cartography.intel.zoom.client import ZoomClient


def response(status, payload):
    result = requests.Response()
    result.status_code = status
    result.json = MagicMock(return_value=payload)
    return result


def test_client_refreshes_expired_token_and_one_401():
    # Arrange
    client = ZoomClient("account-a", "client-id", "secret")
    client.session.post = MagicMock(
        side_effect=[
            response(200, {"access_token": token, "expires_in": 3600})
            for token in ("first", "second", "third")
        ]
    )
    client.session.get = MagicMock(
        side_effect=[
            response(401, {}),
            response(200, {"users": []}),
            response(200, {"users": []}),
        ]
    )

    # Act
    with patch(
        "cartography.intel.zoom.client.time.monotonic",
        side_effect=[0, 0, 0, 3600, 3600],
    ):
        assert client.get_users_page({"status": "active"}) == {"users": []}
        assert client.get_users_page({"status": "inactive"}) == {"users": []}

    # Assert
    assert client.session.post.call_count == 3
    client.session.post.assert_called_with(
        TOKEN_URL,
        data={"grant_type": "account_credentials", "account_id": "account-a"},
        auth=("client-id", "secret"),
        timeout=(10, 60),
        allow_redirects=False,
    )
    assert [
        call.kwargs["headers"]["Authorization"]
        for call in client.session.get.call_args_list
    ] == ["Bearer first", "Bearer second", "Bearer third"]
    assert all(call.args[0] == USERS_URL for call in client.session.get.call_args_list)


def test_client_stops_after_repeated_401():
    # Arrange
    client = ZoomClient("account-a", "client-id", "secret")
    client.session.post = MagicMock(
        return_value=response(200, {"access_token": "token", "expires_in": 3600})
    )
    client.session.get = MagicMock(return_value=response(401, {}))

    # Act and assert
    with pytest.raises(requests.HTTPError):
        client.get_users_page({"status": "active"})
    assert client.session.get.call_count == 2


def test_retry_policy_covers_rate_limits_and_token_issuance():
    # Arrange
    client = ZoomClient("account-a", "client-id", "secret")
    retry = client.session.get_adapter(USERS_URL).max_retries

    # Act and assert
    assert retry.total == 3
    assert retry.respect_retry_after_header
    assert retry.is_retry("GET", 429)
    assert retry.is_retry("POST", 503)
    assert not retry.is_retry("GET", 403)


@pytest.mark.parametrize("endpoint", ["token", "users"])
def test_client_rejects_redirects_even_with_valid_json(endpoint):
    # Arrange
    client = ZoomClient("account-a", "client-id", "secret")
    client.session.post = MagicMock(
        return_value=response(
            302 if endpoint == "token" else 200,
            {"access_token": "token", "expires_in": 3600},
        )
    )
    client.session.get = MagicMock(return_value=response(302, {"users": []}))

    # Act and assert
    with pytest.raises(requests.HTTPError):
        client.get_users_page({"status": "active"})


def test_cli_wires_account_credentials(monkeypatch):
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


def test_unconfigured_module_does_not_request_credentials():
    # Arrange
    config = Config(neo4j_uri="bolt://localhost:7687")

    # Act
    with patch("cartography.intel.zoom.ZoomClient") as client:
        start_zoom_ingestion(MagicMock(), config)

    # Assert
    client.assert_not_called()
