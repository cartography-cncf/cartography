from collections.abc import Callable
from typing import cast
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.tailscale import _attach_oauth_refresh
from cartography.intel.tailscale import _mint_oauth_bearer
from cartography.intel.tailscale import start_tailscale_ingestion


def _make_config(
    *,
    org: str | None = "example.com",
    token: str | None = None,
    oauth_id: str | None = None,
    oauth_secret: str | None = None,
) -> MagicMock:
    config = MagicMock()
    config.tailscale_org = org
    config.tailscale_token = token
    config.tailscale_oauth_client_id = oauth_id
    config.tailscale_oauth_client_secret = oauth_secret
    config.tailscale_base_url = "https://api.tailscale.com/api/v2"
    config.update_tag = 1
    return config


def test_mint_oauth_bearer_posts_client_credentials() -> None:
    api_session = MagicMock(spec=requests.Session)
    api_session.post.return_value.json.return_value = {"access_token": "tskey-abc"}

    token = _mint_oauth_bearer(
        api_session,
        "https://api.tailscale.com/api/v2/",
        "client-id",
        "client-secret",
    )

    assert token == "tskey-abc"
    posted_url, *_ = api_session.post.call_args.args
    assert posted_url == "https://api.tailscale.com/api/v2/oauth/token"
    assert api_session.post.call_args.kwargs["data"] == {
        "grant_type": "client_credentials",
        "client_id": "client-id",
        "client_secret": "client-secret",
    }
    assert api_session.post.call_args.kwargs["headers"]["Authorization"] is None
    assert (
        "X-Cartography-Tailscale-Reauth"
        not in api_session.post.call_args.kwargs["headers"]
    )
    api_session.post.return_value.raise_for_status.assert_called_once()


def test_mint_oauth_bearer_propagates_http_error() -> None:
    api_session = MagicMock(spec=requests.Session)
    api_session.post.return_value.raise_for_status.side_effect = requests.HTTPError(
        "401 invalid_client",
    )

    with pytest.raises(requests.HTTPError):
        _mint_oauth_bearer(
            api_session,
            "https://api.tailscale.com/api/v2",
            "id",
            "wrong-secret",
        )


def _start_full_sync_patches() -> None:
    targets = [
        "tailnets",
        "users",
        "postureintegrations",
        "services",
        "postureresolution",
        "grants",
    ]
    for name in targets:
        patch(f"cartography.intel.tailscale.{name}.sync").start()
    patch(
        "cartography.intel.tailscale.devices.sync",
        return_value=([], []),
    ).start()
    patch(
        "cartography.intel.tailscale.acls.sync",
        return_value=([], [], [], []),
    ).start()


def test_oauth_client_is_minted_when_configured() -> None:
    _start_full_sync_patches()
    try:
        with patch(
            "cartography.intel.tailscale._mint_oauth_bearer",
            return_value="minted-bearer",
        ) as mock_mint:
            start_tailscale_ingestion(
                MagicMock(),
                _make_config(oauth_id="cid", oauth_secret="csecret"),
            )

        assert mock_mint.call_count == 1
        _, base_url, client_id, client_secret = mock_mint.call_args.args
        assert base_url == "https://api.tailscale.com/api/v2"
        assert client_id == "cid"
        assert client_secret == "csecret"
    finally:
        patch.stopall()


def test_oauth_wins_when_both_configured() -> None:
    _start_full_sync_patches()
    try:
        with patch(
            "cartography.intel.tailscale._mint_oauth_bearer",
            return_value="minted-bearer",
        ) as mock_mint:
            start_tailscale_ingestion(
                MagicMock(),
                _make_config(
                    token="static",
                    oauth_id="cid",
                    oauth_secret="csecret",
                ),
            )
        mock_mint.assert_called_once()
    finally:
        patch.stopall()


@patch("cartography.intel.tailscale.tailnets.sync")
@patch("cartography.intel.tailscale._mint_oauth_bearer")
def test_skip_when_only_org_set(
    mock_mint: MagicMock,
    mock_tailnets_sync: MagicMock,
) -> None:
    start_tailscale_ingestion(MagicMock(), _make_config())

    mock_mint.assert_not_called()
    mock_tailnets_sync.assert_not_called()


@patch("cartography.intel.tailscale.tailnets.sync")
@patch("cartography.intel.tailscale._mint_oauth_bearer")
def test_skip_when_only_oauth_client_id_set(
    mock_mint: MagicMock,
    mock_tailnets_sync: MagicMock,
) -> None:
    start_tailscale_ingestion(MagicMock(), _make_config(oauth_id="cid"))

    mock_mint.assert_not_called()
    mock_tailnets_sync.assert_not_called()


def _response(
    status: int,
    url: str = "https://api.tailscale.com/api/v2/tailnet/x/devices",
) -> requests.Response:
    resp = requests.Response()
    resp.status_code = status
    resp.url = url
    resp.raw = MagicMock()
    req = requests.Request("GET", url).prepare()
    resp.request = req
    return resp


def test_refresh_hook_remints_and_retries_on_401() -> None:
    api_session = requests.Session()
    with patch(
        "cartography.intel.tailscale._mint_oauth_bearer",
        return_value="fresh-bearer",
    ) as mock_mint:
        _attach_oauth_refresh(
            api_session,
            "https://api.tailscale.com/api/v2",
            "cid",
            "csecret",
        )
        hook = cast(Callable[..., requests.Response], api_session.hooks["response"][-1])

        original_response = _response(401)
        retried = _response(200)
        with (
            patch.object(original_response, "close") as mock_close,
            patch.object(api_session, "send", return_value=retried) as mock_send,
        ):
            result = hook(original_response, timeout=(5, 30), verify=False)

        mock_mint.assert_called_once()
        assert result is retried
        sent_req = mock_send.call_args.args[0]
        assert sent_req.headers["Authorization"] == "Bearer fresh-bearer"
        assert "X-Cartography-Tailscale-Reauth" not in sent_req.headers
        mock_close.assert_called_once()
        assert mock_send.call_args.kwargs == {"timeout": (5, 30), "verify": False}
        assert api_session.headers["Authorization"] == "Bearer fresh-bearer"


def test_refresh_hook_passes_through_non_401() -> None:
    api_session = requests.Session()
    with patch("cartography.intel.tailscale._mint_oauth_bearer") as mock_mint:
        _attach_oauth_refresh(
            api_session,
            "https://api.tailscale.com/api/v2",
            "cid",
            "csecret",
        )
        hook = api_session.hooks["response"][-1]
        ok = _response(200)
        assert hook(ok) is ok
        mock_mint.assert_not_called()


def test_refresh_hook_does_not_loop_when_retry_also_401s() -> None:
    api_session = requests.Session()
    with patch(
        "cartography.intel.tailscale._mint_oauth_bearer",
        return_value="fresh-bearer",
    ) as mock_mint:
        _attach_oauth_refresh(
            api_session,
            "https://api.tailscale.com/api/v2",
            "cid",
            "csecret",
        )
        hook = cast(Callable[..., requests.Response], api_session.hooks["response"][-1])

        def _send_retry(request: requests.PreparedRequest) -> requests.Response:
            retry_response = _response(401)
            retry_response.request = request
            return hook(retry_response)

        with patch.object(api_session, "send", side_effect=_send_retry):
            result = hook(_response(401))

        assert result.status_code == 401
        mock_mint.assert_called_once()


def test_refresh_hook_ignores_401_from_token_endpoint() -> None:
    api_session = requests.Session()
    with patch("cartography.intel.tailscale._mint_oauth_bearer") as mock_mint:
        _attach_oauth_refresh(
            api_session,
            "https://api.tailscale.com/api/v2",
            "cid",
            "csecret",
        )
        hook = api_session.hooks["response"][-1]
        mint_resp = _response(401, url="https://api.tailscale.com/api/v2/oauth/token")
        assert hook(mint_resp) is mint_resp
        mock_mint.assert_not_called()
