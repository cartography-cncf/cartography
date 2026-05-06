from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

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
