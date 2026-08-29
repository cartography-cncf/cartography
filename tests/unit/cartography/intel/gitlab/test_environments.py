"""Unit tests for GitLab environments module."""

from unittest.mock import Mock
from unittest.mock import patch

import requests

from cartography.intel.gitlab.environments import get_environments
from cartography.intel.gitlab.environments import transform_environments
from tests.data.gitlab.environments import GET_ENVIRONMENTS_RESPONSE
from tests.data.gitlab.environments import TEST_GITLAB_URL
from tests.data.gitlab.environments import TEST_PROJECT_ID


def _http_error(status_code: int) -> requests.exceptions.HTTPError:
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    return requests.exceptions.HTTPError(response=response)


def test_transform_environments_uses_composite_id():
    """Composite id encodes project_id so envs across projects don't collide."""
    transformed = transform_environments(
        GET_ENVIRONMENTS_RESPONSE, TEST_PROJECT_ID, TEST_GITLAB_URL
    )
    ids = {e["id"] for e in transformed}
    assert ids == {
        f"{TEST_PROJECT_ID}:1",
        f"{TEST_PROJECT_ID}:2",
        f"{TEST_PROJECT_ID}:3",
    }


def test_transform_environments_drops_entries_without_id():
    transformed = transform_environments(
        [{"name": "no-id"}], TEST_PROJECT_ID, TEST_GITLAB_URL
    )
    assert transformed == []


def _vars(specs):
    """Build minimal variable dicts: list of (id, key, environment_scope)."""
    return [
        {"id": vid, "key": key, "environment_scope": scope} for vid, key, scope in specs
    ]


def _envs(specs):
    """Build raw GitLab API env entries: list of (id, name)."""
    return [{"id": eid, "name": name} for eid, name in specs]


def _linked_ids(transformed):
    """Map env name -> list of linked variable ids, for tidy assertions."""
    return {env["name"]: env["linked_variable_ids"] for env in transformed}


def test_transform_environments_exact_scope_match():
    raw_envs = _envs([(1, "production")])
    variables = _vars([("v1", "DB_URL", "production"), ("v2", "DB_URL", "staging")])
    transformed = transform_environments(
        raw_envs, TEST_PROJECT_ID, TEST_GITLAB_URL, variables
    )
    assert _linked_ids(transformed) == {"production": ["v1"]}


def test_transform_environments_wildcard_scope_links_all_envs():
    raw_envs = _envs([(1, "production"), (2, "staging")])
    variables = _vars([("v1", "FEATURE_FLAG", "*")])
    transformed = transform_environments(
        raw_envs, TEST_PROJECT_ID, TEST_GITLAB_URL, variables
    )
    assert _linked_ids(transformed) == {"production": ["v1"], "staging": ["v1"]}


def test_transform_environments_mixed_exact_and_wildcard():
    raw_envs = _envs([(1, "production"), (2, "staging")])
    variables = _vars(
        [
            ("v1", "DB_URL", "production"),
            ("v2", "DB_URL", "staging"),
            ("v3", "FEATURE_FLAG", "*"),
        ]
    )
    transformed = transform_environments(
        raw_envs, TEST_PROJECT_ID, TEST_GITLAB_URL, variables
    )
    assert _linked_ids(transformed) == {
        "production": ["v1", "v3"],
        "staging": ["v2", "v3"],
    }


def test_transform_environments_no_matching_variable():
    raw_envs = _envs([(1, "production")])
    variables = _vars([("v1", "X", "staging")])
    transformed = transform_environments(
        raw_envs, TEST_PROJECT_ID, TEST_GITLAB_URL, variables
    )
    assert _linked_ids(transformed) == {"production": []}


def test_transform_environments_glob_pattern_does_not_match():
    """v1 has scope 'production/*' — GitLab expands it at runtime, but we don't."""
    raw_envs = _envs([(1, "production/web")])
    variables = _vars([("v1", "X", "production/*")])
    transformed = transform_environments(
        raw_envs, TEST_PROJECT_ID, TEST_GITLAB_URL, variables
    )
    assert _linked_ids(transformed) == {"production/web": []}


@patch("cartography.intel.gitlab.environments.get_paginated")
def test_get_environments_returns_none_on_403(mock_get_paginated):
    """Sentinel ``None`` so the caller can skip both load and cleanup."""
    mock_get_paginated.side_effect = _http_error(403)
    assert get_environments(TEST_GITLAB_URL, "tok", TEST_PROJECT_ID) is None


@patch("cartography.intel.gitlab.environments.get_paginated")
def test_get_environments_returns_empty_on_404(mock_get_paginated):
    """A 404 means "project has no environments feature" — non-fatal, [] not None."""
    mock_get_paginated.side_effect = _http_error(404)
    assert get_environments(TEST_GITLAB_URL, "tok", TEST_PROJECT_ID) == []


@patch("cartography.intel.gitlab.environments.get_paginated")
def test_get_environments_propagates_500(mock_get_paginated):
    mock_get_paginated.side_effect = _http_error(500)
    try:
        get_environments(TEST_GITLAB_URL, "tok", TEST_PROJECT_ID)
        raise AssertionError("Expected HTTPError to propagate")
    except requests.exceptions.HTTPError:
        pass
