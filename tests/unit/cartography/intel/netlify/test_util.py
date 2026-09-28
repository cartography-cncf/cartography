from unittest import mock

import pytest
import requests

from cartography.intel.netlify.util import get_list
from cartography.intel.netlify.util import get_one
from cartography.intel.netlify.util import NetlifyPaginationError
from cartography.intel.netlify.util import NetlifyPlanGatedError
from cartography.intel.netlify.util import paginated_get
from cartography.intel.netlify.util import unwrap_extended_json

_URL = "https://api.netlify.com/api/v1/example-team/sites"


def _response(
    body,
    status_code: int = 200,
    next_url: str | None = None,
    headers: dict | None = None,
) -> mock.MagicMock:
    response = mock.MagicMock(spec=requests.Response)
    response.status_code = status_code
    response.headers = headers or {}
    response.links = {"next": {"url": next_url}} if next_url else {}
    response.json.return_value = body
    response.raise_for_status.return_value = None
    return response


def _session(*responses) -> mock.MagicMock:
    session = mock.MagicMock(spec=requests.Session)
    session.get.side_effect = list(responses)
    return session


def test_paginated_get_walks_the_link_header():
    page2 = f"{_URL}?page=2&per_page=100"
    session = _session(
        _response([{"id": "a"}], next_url=page2),
        _response([{"id": "b"}]),
    )

    assert paginated_get(session, _URL) == [{"id": "a"}, {"id": "b"}]
    assert [call.args[0] for call in session.get.call_args_list] == [_URL, page2]


def test_paginated_get_sends_params_on_the_first_request_only():
    """
    The Link URL already carries `page` and `per_page`. Re-sending our own params would fight the
    cursor and could pin the loop to page one forever.
    """
    page2 = f"{_URL}?page=2&per_page=100"
    session = _session(
        _response([{"id": "a"}], next_url=page2),
        _response([{"id": "b"}]),
    )

    paginated_get(session, _URL, params={"account_slug": "example-team"})

    first, second = session.get.call_args_list
    assert first.kwargs["params"] == {
        "per_page": 100,
        "account_slug": "example-team",
    }
    assert second.kwargs["params"] is None


def test_paginated_get_stops_on_the_last_page():
    session = _session(_response([{"id": "a"}]))
    assert paginated_get(session, _URL) == [{"id": "a"}]
    assert session.get.call_count == 1


def test_paginated_get_treats_a_null_body_as_empty():
    session = _session(_response(None))
    assert paginated_get(session, _URL) == []


def test_paginated_get_raises_when_the_next_link_points_at_the_current_page():
    """
    A page that advertises a successor it cannot reach must never be downgraded to
    warning-and-stop: the cleanup jobs treat the returned list as the exhaustive set of live
    resources, so a short list deletes everything past the last page read.
    """
    session = _session(_response([{"id": "a"}], next_url=_URL))

    with pytest.raises(NetlifyPaginationError, match="points back at the current page"):
        paginated_get(session, _URL)


def test_paginated_get_raises_on_an_empty_next_link():
    session = _session(_response([{"id": "a"}], next_url=""))

    # An empty url is falsy, so requests reports no next link at all and the walk simply ends.
    assert paginated_get(session, _URL) == [{"id": "a"}]


def test_paginated_get_rejects_an_off_origin_next_link():
    """
    The session carries the bearer token on every request, so following a link to another host
    would hand the Netlify token to whoever the header named.
    """
    session = _session(
        _response([{"id": "a"}], next_url="https://attacker.example/collect?page=2"),
    )

    with pytest.raises(NetlifyPaginationError, match="different origin"):
        paginated_get(session, _URL)


def test_paginated_get_resolves_a_relative_next_link():
    session = _session(
        _response([{"id": "a"}], next_url="/api/v1/example-team/sites?page=2"),
        _response([{"id": "b"}]),
    )

    assert paginated_get(session, _URL) == [{"id": "a"}, {"id": "b"}]
    assert (
        session.get.call_args_list[1].args[0]
        == "https://api.netlify.com/api/v1/example-team/sites?page=2"
    )


def test_paginated_get_raises_when_the_body_is_not_an_array():
    """
    Same reasoning: a misread response must surface rather than reach cleanup as an empty set.
    """
    session = _session(_response({"sites": [{"id": "a"}]}))

    with pytest.raises(NetlifyPaginationError, match="Expected a JSON array"):
        paginated_get(session, _URL)


def test_paginated_get_returns_empty_on_404_when_allowed():
    session = _session(_response(None, status_code=404))
    assert paginated_get(session, _URL, allow_missing=True) == []


def test_paginated_get_raises_on_404_by_default():
    response = _response(None, status_code=404)
    response.raise_for_status.side_effect = requests.HTTPError("404")
    session = _session(response)

    with pytest.raises(requests.HTTPError):
        paginated_get(session, _URL)


def test_paginated_get_returns_partial_on_a_plan_gated_403():
    page2 = f"{_URL}?page=2&per_page=100"
    session = _session(
        _response([{"id": "a"}], next_url=page2),
        _response(None, status_code=403),
    )

    assert paginated_get(session, _URL, allow_plan_gated=True) == [{"id": "a"}]


def test_paginated_get_raises_on_403_by_default():
    """
    A 403 must not silently become an empty result: the caller has to decide, because an empty
    list reaching cleanup deletes whatever a previous run on a higher plan had ingested.
    """
    session = _session(_response(None, status_code=403))

    with pytest.raises(NetlifyPlanGatedError, match="403 Forbidden"):
        paginated_get(session, _URL)


def test_paginated_get_warns_when_the_rate_limit_is_nearly_exhausted(caplog):
    session = _session(
        _response([{"id": "a"}], headers={"X-RateLimit-Remaining": "3"}),
    )

    with caplog.at_level("WARNING"):
        paginated_get(session, _URL)

    assert "rate limit is nearly exhausted" in caplog.text


def test_paginated_get_ignores_an_unparseable_rate_limit_header(caplog):
    session = _session(
        _response([{"id": "a"}], headers={"X-RateLimit-Remaining": "unknown"}),
    )

    with caplog.at_level("WARNING"):
        assert paginated_get(session, _URL) == [{"id": "a"}]

    assert "rate limit" not in caplog.text


def test_get_list_unwraps_an_envelope():
    session = _session(_response({"branches": [{"branch_id": "production"}]}))
    assert get_list(session, _URL, result_key="branches") == [
        {"branch_id": "production"},
    ]


def test_get_list_raises_when_the_envelope_is_missing():
    """
    Strict access: an endpoint that stopped using the envelope must surface, not silently hand an
    empty list to a cleanup job.
    """
    session = _session(_response([{"branch_id": "production"}]))

    with pytest.raises(ValueError, match="Expected a JSON object with key 'branches'"):
        get_list(session, _URL, result_key="branches")


def test_get_list_wraps_a_bare_object():
    """
    The site functions endpoint answers with a bare object when there is a single bundle.
    """
    session = _session(_response({"id": "bundle", "functions": []}))
    assert get_list(session, _URL) == [{"id": "bundle", "functions": []}]


def test_get_list_treats_an_empty_object_as_an_empty_collection():
    """
    A site with no functions answers `200 {}`. Verified against the live API, both on a site that
    had never been deployed and on one deployed without any functions. Wrapping that into `[{}]`
    would hand a phantom bundle to the transform.
    """
    session = _session(_response({}))
    assert get_list(session, _URL) == []


def test_get_list_raises_on_404_by_default():
    """
    Netlify answers an empty array, not a 404, for a resource a site simply does not have, so a
    404 here is a failed read and must not reach cleanup as "the team has none".
    """
    response = _response(None, status_code=404)
    response.raise_for_status.side_effect = requests.HTTPError("404")
    session = _session(response)

    with pytest.raises(requests.HTTPError):
        get_list(session, _URL)


def test_get_list_returns_empty_on_404_when_explicitly_allowed():
    session = _session(_response(None, status_code=404))
    assert get_list(session, _URL, allow_missing=True) == []


def test_get_one_returns_none_on_a_null_body():
    """
    A site with no custom domain answers the TLS endpoint with `null`, not a 404.
    """
    session = _session(_response(None))
    assert get_one(session, _URL) is None


def test_get_one_returns_none_on_404():
    session = _session(_response(None, status_code=404))
    assert get_one(session, _URL) is None


def test_get_one_raises_when_the_body_is_not_an_object():
    session = _session(_response([{"id": "a"}]))

    with pytest.raises(ValueError, match="Expected a JSON object"):
        get_one(session, _URL)


@pytest.mark.parametrize(
    "value,expected",
    [
        ({"$oid": "6a99a33f1815565afdc2d4be"}, "6a99a33f1815565afdc2d4be"),
        ({"$date": "2026-07-30T15:32:17.370Z"}, "2026-07-30T15:32:17.370Z"),
        ({"$numberLong": 12}, 12),
        # Left alone: a real object, a wrapper we do not know, and plain scalars.
        ({"google": "alice@example.com"}, {"google": "alice@example.com"}),
        ({"$unknown": "x"}, {"$unknown": "x"}),
        ({"$oid": {"nested": "x"}}, {"$oid": {"nested": "x"}}),
        ({"$oid": "a", "$date": "b"}, {"$oid": "a", "$date": "b"}),
        ("plain-string-id", "plain-string-id"),
        (None, None),
    ],
)
def test_unwrap_extended_json(value, expected):
    """
    Netlify leaks MongoDB's extended JSON on some fields, and Neo4j refuses a map as a property
    value, so the wrapper has to be reduced to its scalar before the payload reaches a load.
    """
    assert unwrap_extended_json(value) == expected
