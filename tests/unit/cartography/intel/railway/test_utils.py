from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from cartography.intel.railway.utils import build_tcp_proxy_batch_query
from cartography.intel.railway.utils import call_railway_api
from cartography.intel.railway.utils import is_live_entrypoint
from cartography.intel.railway.utils import paginated_query
from cartography.intel.railway.utils import RailwayGraphQLError
from cartography.intel.railway.utils import RailwayPaginationError
from cartography.intel.railway.utils import unwrap_edges

BASE_URL = "https://backboard.railway.com/graphql/v2"
SERVICE_ID = "66666666-6666-6666-6666-666666666666"
ENVIRONMENT_ID = "44444444-4444-4444-4444-444444444444"


def _response(
    json_body: dict,
    status_code: int = 200,
    headers: dict | None = None,
) -> MagicMock:
    response = MagicMock(spec=requests.Response)
    response.status_code = status_code
    response.headers = headers or {}
    response.json.return_value = json_body
    response.raise_for_status.return_value = None
    return response


def _session(*responses: MagicMock) -> MagicMock:
    session = MagicMock(spec=requests.Session)
    session.post.side_effect = list(responses)
    return session


def test_call_railway_api_returns_data():
    session = _session(_response({"data": {"me": {"id": "u1"}}}))

    assert call_railway_api(session, BASE_URL, "query Me { me { id } }") == {
        "me": {"id": "u1"},
    }


def test_call_railway_api_raises_on_graphql_errors():
    # Railway answers HTTP 200 with a populated `errors` array on auth failure. Treating that
    # as an empty result would let cleanup delete the whole workspace.
    session = _session(
        _response({"data": None, "errors": [{"message": "Not Authorized"}]}),
    )

    with pytest.raises(RailwayGraphQLError, match="Not Authorized"):
        call_railway_api(session, BASE_URL, "query Me { me { id } }")


def test_railway_graphql_error_detects_authorization_failures():
    unauthorized = RailwayGraphQLError([{"message": "Not Authorized"}])
    other = RailwayGraphQLError([{"message": "Problem processing request"}])
    mixed = RailwayGraphQLError(
        [{"message": "Not Authorized"}, {"message": "Problem processing request"}],
    )

    assert unauthorized.is_not_authorized is True
    assert other.is_not_authorized is False
    assert mixed.is_not_authorized is False


@patch("cartography.intel.railway.utils.time.sleep")
def test_call_railway_api_retries_after_429(mock_sleep):
    session = _session(
        _response({}, status_code=429, headers={"Retry-After": "7"}),
        _response({"data": {"me": {"id": "u1"}}}),
    )

    assert call_railway_api(session, BASE_URL, "query Me { me { id } }") == {
        "me": {"id": "u1"},
    }
    mock_sleep.assert_called_once_with(7)


@patch("cartography.intel.railway.utils.time.sleep")
def test_call_railway_api_raises_when_backoff_exceeds_cap(mock_sleep):
    # An hour-long window means a huge Retry-After should fail loudly rather than stall.
    session = _session(_response({}, status_code=429, headers={"Retry-After": "3000"}))

    with pytest.raises(RuntimeError, match="rate limit exhausted"):
        call_railway_api(session, BASE_URL, "query Me { me { id } }")
    mock_sleep.assert_not_called()


def test_unwrap_edges():
    connection = {"edges": [{"node": {"id": "a"}}, {"node": {"id": "b"}}]}

    assert unwrap_edges(connection) == [{"id": "a"}, {"id": "b"}]


def test_paginated_query_walks_every_page():
    page_one = _response(
        {
            "data": {
                "projects": {
                    "edges": [{"node": {"id": "p1"}}],
                    "pageInfo": {"hasNextPage": True, "endCursor": "cursor1"},
                },
            },
        },
    )
    page_two = _response(
        {
            "data": {
                "projects": {
                    "edges": [{"node": {"id": "p2"}}],
                    "pageInfo": {"hasNextPage": False, "endCursor": "cursor2"},
                },
            },
        },
    )
    session = _session(page_one, page_two)

    results = paginated_query(session, BASE_URL, "query {}", {}, ("projects",))

    assert results == [{"id": "p1"}, {"id": "p2"}]
    assert session.post.call_args_list[0].kwargs["json"]["variables"]["after"] is None
    assert (
        session.post.call_args_list[1].kwargs["json"]["variables"]["after"] == "cursor1"
    )


def test_paginated_query_raises_on_missing_cursor():
    # A page claiming more results but giving no cursor cannot be completed. Returning what
    # we have would let a cleanup job treat it as exhaustive and delete the rest.
    stuck_page = {
        "data": {
            "projects": {
                "edges": [{"node": {"id": "p1"}}],
                "pageInfo": {"hasNextPage": True, "endCursor": None},
            },
        },
    }
    session = _session(_response(stuck_page), _response(stuck_page))

    with pytest.raises(RailwayPaginationError, match="unusable endCursor"):
        paginated_query(session, BASE_URL, "query {}", {}, ("projects",))
    assert session.post.call_count == 1


def test_paginated_query_raises_on_unchanged_cursor():
    # Same reasoning: a repeated cursor would loop over page one forever.
    stuck_page = {
        "data": {
            "projects": {
                "edges": [{"node": {"id": "p1"}}],
                "pageInfo": {"hasNextPage": True, "endCursor": "cursor-1"},
            },
        },
    }
    session = _session(_response(stuck_page), _response(stuck_page))

    with pytest.raises(RailwayPaginationError, match="unusable endCursor"):
        paginated_query(
            session,
            BASE_URL,
            "query {}",
            {},
            ("projects",),
            after="cursor-1",
        )


def test_paginated_query_walks_a_nested_connection_path():
    session = _session(
        _response(
            {
                "data": {
                    "project": {
                        "services": {
                            "edges": [{"node": {"id": "s1"}}],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        },
                    },
                },
            },
        ),
    )

    results = paginated_query(
        session,
        BASE_URL,
        "query {}",
        {"projectId": "p1"},
        ("project", "services"),
    )

    assert results == [{"id": "s1"}]


def test_build_tcp_proxy_batch_query_aliases_each_pair():
    query = build_tcp_proxy_batch_query(
        [(SERVICE_ID, ENVIRONMENT_ID), (ENVIRONMENT_ID, SERVICE_ID)],
    )

    assert f'p0: tcpProxies(serviceId: "{SERVICE_ID}"' in query
    assert f'p1: tcpProxies(serviceId: "{ENVIRONMENT_ID}"' in query


def test_build_tcp_proxy_batch_query_rejects_non_uuid_input():
    with pytest.raises(ValueError, match="non-UUID value"):
        build_tcp_proxy_batch_query([('") { id } injected(x: "', ENVIRONMENT_ID)])


def test_is_live_entrypoint_only_accepts_serving_states():
    # Railway keeps domain and proxy rows around through their whole lifecycle. Only a
    # serving one is exposure; counting the rest would over-report the attack surface.
    assert is_live_entrypoint({"syncStatus": "ACTIVE"}) is True
    assert is_live_entrypoint({"syncStatus": "UPDATING"}) is True
    for dead in ("CREATING", "DELETING", "DELETED", "UNSPECIFIED"):
        assert is_live_entrypoint({"syncStatus": dead}) is False, dead
    # A missing status is not evidence of serving.
    assert is_live_entrypoint({}) is False


def test_is_live_entrypoint_requires_custom_domain_verification():
    # A custom domain that has not passed DNS verification does not resolve, even ACTIVE.
    assert (
        is_live_entrypoint(
            {"syncStatus": "ACTIVE", "status": {"verified": False}},
        )
        is False
    )
    assert (
        is_live_entrypoint(
            {"syncStatus": "ACTIVE", "status": {"verified": True}},
        )
        is True
    )
