from unittest.mock import Mock

import pytest
import requests

from cartography.intel.bitbucket.auth import BearerTokenCredential
from cartography.intel.bitbucket.util import get_paginated


def _make_response(json_data):
    response = Mock(spec=requests.Response)
    response.status_code = 200
    response.raise_for_status.return_value = None
    response.json.return_value = json_data
    return response


def test_get_paginated_follows_next_url(monkeypatch):
    page_1 = _make_response(
        {"values": [{"id": 1}], "next": "https://api.bitbucket.org/2.0/next-page"}
    )
    page_2 = _make_response({"values": [{"id": 2}], "next": None})
    responses = iter([page_1, page_2])
    requested_urls = []

    def _request(method, url, headers=None, params=None, timeout=None):
        requested_urls.append((url, params))
        return next(responses)

    monkeypatch.setattr("cartography.intel.bitbucket.util.requests.request", _request)

    credential = BearerTokenCredential("fake-token")
    result = get_paginated(credential, "/workspaces")

    assert result == [{"id": 1}, {"id": 2}]
    assert requested_urls[0][0] == "https://api.bitbucket.org/2.0/workspaces"
    assert requested_urls[0][1] is not None  # first request carries pagelen params
    assert requested_urls[1][0] == "https://api.bitbucket.org/2.0/next-page"
    assert requested_urls[1][1] is None  # `next` already encodes cursor state


def test_get_paginated_stops_when_no_next(monkeypatch):
    page = _make_response({"values": [{"id": 1}], "next": None})
    monkeypatch.setattr(
        "cartography.intel.bitbucket.util.requests.request",
        lambda *args, **kwargs: page,
    )

    credential = BearerTokenCredential("fake-token")
    result = get_paginated(credential, "/workspaces")

    assert result == [{"id": 1}]


def test_get_paginated_rejects_empty_next(monkeypatch):
    page = _make_response({"values": [{"id": 1}], "next": ""})
    monkeypatch.setattr(
        "cartography.intel.bitbucket.util.requests.request",
        lambda *args, **kwargs: page,
    )

    with pytest.raises(ValueError, match="Malformed"):
        get_paginated(BearerTokenCredential("fake-token"), "/workspaces")
