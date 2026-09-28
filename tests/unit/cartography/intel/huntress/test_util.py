from typing import Any
from unittest.mock import MagicMock

import pytest
import requests
from requests.adapters import HTTPAdapter

from cartography.intel.huntress.util import create_huntress_api_session
from cartography.intel.huntress.util import get_huntress_item
from cartography.intel.huntress.util import get_paginated_huntress_items
from cartography.intel.huntress.util import required_id

TEST_BASE_URI = "https://api.huntress.io"


def _response(payload: dict[str, Any]) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    return response


def test_create_huntress_api_session_uses_basic_auth() -> None:
    session = create_huntress_api_session("hk_key", "hs_secret")

    assert session.auth == ("hk_key", "hs_secret")
    adapter = session.get_adapter("https://api.huntress.io")
    assert isinstance(adapter, HTTPAdapter)
    retries = adapter.max_retries
    assert 429 in retries.status_forcelist


def test_get_paginated_huntress_items_follows_the_page_token() -> None:
    api_session = MagicMock()
    api_session.get.side_effect = [
        _response(
            {
                "agents": [{"id": 1}, {"id": 2}],
                "pagination": {"next_page_token": "token-2"},
            }
        ),
        _response({"agents": [{"id": 3}], "pagination": {"next_page_token": None}}),
    ]

    result = get_paginated_huntress_items(
        api_session, TEST_BASE_URI, "agents", "agents"
    )

    assert result == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert api_session.get.call_args_list[0].args == (
        "https://api.huntress.io/v1/agents",
    )
    assert "page_token" not in api_session.get.call_args_list[0].kwargs["params"]
    assert api_session.get.call_args_list[1].kwargs["params"]["page_token"] == "token-2"


def test_get_paginated_huntress_items_stops_without_a_pagination_object() -> None:
    """The API omits `next_page_token` when the whole collection fits in one page."""
    api_session = MagicMock()
    api_session.get.return_value = _response(
        {
            "organizations": [{"id": 1}],
            "pagination": {"current_page": 1, "total_count": 1},
        }
    )

    result = get_paginated_huntress_items(
        api_session, TEST_BASE_URI, "organizations", "organizations"
    )

    assert result == [{"id": 1}]
    assert api_session.get.call_count == 1


def test_get_paginated_huntress_items_rejects_a_repeated_page_token() -> None:
    api_session = MagicMock()
    api_session.get.return_value = _response(
        {"agents": [{"id": 1}], "pagination": {"next_page_token": "stuck"}}
    )

    with pytest.raises(ValueError, match="repeated page token"):
        get_paginated_huntress_items(api_session, TEST_BASE_URI, "agents", "agents")


def test_get_paginated_huntress_items_rejects_a_body_without_the_collection() -> None:
    """An unexpected 200 body must not look like an empty page, or cleanup would wipe."""
    api_session = MagicMock()
    api_session.get.return_value = _response({"error": "something went sideways"})

    with pytest.raises(ValueError, match="without the expected 'agents' collection"):
        get_paginated_huntress_items(api_session, TEST_BASE_URI, "agents", "agents")


def test_get_paginated_huntress_items_propagates_http_errors() -> None:
    api_session = MagicMock()
    response = MagicMock()
    response.raise_for_status.side_effect = requests.exceptions.HTTPError("403")
    api_session.get.return_value = response

    with pytest.raises(requests.exceptions.HTTPError):
        get_paginated_huntress_items(
            api_session, TEST_BASE_URI, "memberships", "memberships"
        )


def test_get_huntress_item_returns_the_wrapped_object() -> None:
    api_session = MagicMock()
    api_session.get.return_value = _response({"account": {"id": 1000}})

    assert get_huntress_item(api_session, TEST_BASE_URI, "account", "account") == {
        "id": 1000
    }


def test_get_huntress_item_rejects_a_body_without_the_object() -> None:
    api_session = MagicMock()
    api_session.get.return_value = _response({"error": "nope"})

    with pytest.raises(ValueError, match="without the expected 'account' object"):
        get_huntress_item(api_session, TEST_BASE_URI, "account", "account")


@pytest.mark.parametrize("bad_id", [None, "", "  ", "3001", 3.5, True, []])
def test_required_id_rejects_an_unusable_id(bad_id):
    """The id becomes the graph identity, so a blank one would collapse nodes together."""
    with pytest.raises(ValueError, match="id is not an integer"):
        required_id({"id": bad_id}, "Agent")


def test_required_id_raises_when_the_key_is_absent() -> None:
    with pytest.raises(KeyError):
        required_id({"hostname": "homer-desktop"}, "Agent")


def test_required_id_returns_the_integer() -> None:
    assert required_id({"id": 3001}, "Agent") == 3001
