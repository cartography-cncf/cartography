"""
A truncated project bundle must never reach the transforms.

Every connection in PROJECT_BUNDLE_QUERY is capped at `first: $first`. The cleanup jobs
treat whatever they are handed as the exhaustive set, so a bundle that silently stopped at
the first page would make them delete every resource past it.
"""

from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.railway.projects
from cartography.intel.railway.queries import ENVIRONMENT_CHILD_QUERIES
from cartography.intel.railway.queries import PROJECT_CHILD_QUERIES

BASE_URL = "https://backboard.railway.com/graphql/v2"
PROJECT_ID = "33333333-3333-3333-3333-333333333333"
ENV_ID = "44444444-4444-4444-4444-444444444444"


def _connection(node_ids, has_next_page=False, end_cursor=None):
    return {
        "edges": [{"node": {"id": node_id}} for node_id in node_ids],
        "pageInfo": {"hasNextPage": has_next_page, "endCursor": end_cursor},
    }


def _environment(env_id, **child_overrides):
    environment = {"id": env_id, "name": "production"}
    for key in ENVIRONMENT_CHILD_QUERIES:
        environment[key] = child_overrides.get(key, _connection([]))
    return environment


def _bundle(environments, **project_overrides):
    bundle = {
        "id": PROJECT_ID,
        "environments": {
            "edges": [{"node": env} for env in environments],
            "pageInfo": {"hasNextPage": False, "endCursor": None},
        },
    }
    for key in PROJECT_CHILD_QUERIES:
        bundle[key] = project_overrides.get(key, _connection([]))
    return bundle


def test_drain_is_a_noop_when_nothing_is_truncated():
    bundle = _bundle([_environment(ENV_ID)])

    with patch.object(
        cartography.intel.railway.projects,
        "paginated_query",
    ) as mock_paginated:
        cartography.intel.railway.projects.drain_project_bundle(
            Mock(),
            BASE_URL,
            bundle,
        )

    # A project that fits in one page must cost no extra requests.
    mock_paginated.assert_not_called()


def test_drain_completes_a_truncated_project_connection():
    bundle = _bundle(
        [_environment(ENV_ID)],
        services=_connection(["svc-1"], has_next_page=True, end_cursor="cursor-1"),
    )

    with patch.object(
        cartography.intel.railway.projects,
        "paginated_query",
        return_value=[{"id": "svc-2"}, {"id": "svc-3"}],
    ) as mock_paginated:
        cartography.intel.railway.projects.drain_project_bundle(
            Mock(),
            BASE_URL,
            bundle,
        )

    assert [edge["node"]["id"] for edge in bundle["services"]["edges"]] == [
        "svc-1",
        "svc-2",
        "svc-3",
    ]
    # The follow-up resumes from where the bundle stopped, rather than refetching page one.
    assert mock_paginated.call_args.kwargs["after"] == "cursor-1"
    # And the connection now reports itself complete.
    assert bundle["services"]["pageInfo"]["hasNextPage"] is False


def test_drain_completes_a_truncated_environment_child_connection():
    bundle = _bundle(
        [
            _environment(
                ENV_ID,
                serviceInstances=_connection(
                    ["si-1"],
                    has_next_page=True,
                    end_cursor="cursor-si",
                ),
            ),
        ],
    )

    with patch.object(
        cartography.intel.railway.projects,
        "paginated_query",
        return_value=[{"id": "si-2"}],
    ):
        cartography.intel.railway.projects.drain_project_bundle(
            Mock(),
            BASE_URL,
            bundle,
        )

    environment = bundle["environments"]["edges"][0]["node"]
    assert [
        edge["node"]["id"] for edge in environment["serviceInstances"]["edges"]
    ] == [
        "si-1",
        "si-2",
    ]


def test_drain_recurses_into_environments_fetched_by_the_follow_up():
    # An extra environment arriving from the follow-up query can itself have truncated
    # children, so the child-draining loop has to cover it too.
    extra_environment = _environment(
        "extra-env",
        variables=_connection(["var-1"], has_next_page=True, end_cursor="cursor-var"),
    )
    bundle = _bundle([_environment(ENV_ID)])
    bundle["environments"]["pageInfo"] = {
        "hasNextPage": True,
        "endCursor": "cursor-env",
    }

    def fake_paginated(_session, _url, _query, variables, connection_path, **kwargs):
        if connection_path == ("project", "environments"):
            return [extra_environment]
        if connection_path == ("environment", "variables"):
            assert variables["environmentId"] == "extra-env"
            return [{"id": "var-2"}]
        return []

    with patch.object(
        cartography.intel.railway.projects,
        "paginated_query",
        side_effect=fake_paginated,
    ):
        cartography.intel.railway.projects.drain_project_bundle(
            Mock(),
            BASE_URL,
            bundle,
        )

    environments = [edge["node"] for edge in bundle["environments"]["edges"]]
    assert [env["id"] for env in environments] == [ENV_ID, "extra-env"]
    assert [edge["node"]["id"] for edge in extra_environment["variables"]["edges"]] == [
        "var-1",
        "var-2",
    ]


def test_get_project_bundle_drains_before_returning():
    # The public entry point must never hand a truncated bundle to the transforms.
    raw = _bundle(
        [_environment(ENV_ID)],
        volumes=_connection(["vol-1"], has_next_page=True, end_cursor="cursor-vol"),
    )

    with patch.object(
        cartography.intel.railway.projects,
        "call_railway_api",
        return_value={"project": raw},
    ):
        with patch.object(
            cartography.intel.railway.projects,
            "paginated_query",
            return_value=[{"id": "vol-2"}],
        ):
            bundle = cartography.intel.railway.projects.get_project_bundle(
                Mock(),
                BASE_URL,
                PROJECT_ID,
            )

    assert [edge["node"]["id"] for edge in bundle["volumes"]["edges"]] == [
        "vol-1",
        "vol-2",
    ]


def test_every_paginated_bundle_connection_has_a_follow_up_query():
    # Guard against adding a connection to the bundle without a way to page through it.
    from cartography.intel.railway.queries import PROJECT_BUNDLE_QUERY

    project_connections = {"environments"} | set(PROJECT_CHILD_QUERIES)
    for key in project_connections | set(ENVIRONMENT_CHILD_QUERIES):
        assert f"{key}(first: $first)" in PROJECT_BUNDLE_QUERY, key
