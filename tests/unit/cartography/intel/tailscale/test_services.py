from unittest.mock import MagicMock

import requests

from cartography.intel.tailscale.services import get
from cartography.intel.tailscale.services import transform


def test_transform_preserves_prefixed_service_name() -> None:
    result = transform(
        [
            {
                "name": "svc:web-server",
                "addrs": ["100.100.100.1", "fd7a:115c:a1e0::1"],
                "ports": ["tcp:443"],
                "tags": ["tag:prod"],
            }
        ]
    )

    assert result[0]["id"] == "svc:web-server"
    assert result[0]["name"] == "svc:web-server"


def test_transform_adds_prefix_for_bare_service_name() -> None:
    result = transform(
        [
            {
                "name": "web-server",
                "addrs": ["100.100.100.1", "fd7a:115c:a1e0::1"],
                "ports": ["tcp:443"],
                "tags": ["tag:prod"],
            }
        ]
    )

    assert result[0]["id"] == "svc:web-server"
    assert result[0]["name"] == "web-server"


def test_get_returns_empty_list_on_404() -> None:
    response = MagicMock(spec=requests.Response)
    response.status_code = 404
    api_session = MagicMock(spec=requests.Session)
    api_session.get.return_value = response

    result = get(api_session, "https://api.tailscale.com/api/v2", "example.com")

    assert result == []
    response.raise_for_status.assert_not_called()


def test_get_raises_on_non_404_error() -> None:
    response = MagicMock(spec=requests.Response)
    response.status_code = 500
    response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "500 Server Error",
        response=response,
    )
    api_session = MagicMock(spec=requests.Session)
    api_session.get.return_value = response

    try:
        get(api_session, "https://api.tailscale.com/api/v2", "example.com")
    except requests.exceptions.HTTPError:
        return
    raise AssertionError("expected HTTPError to propagate for non-404 status")
