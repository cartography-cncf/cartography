"""Unit tests for GitLab environments module."""

from unittest.mock import Mock
from unittest.mock import patch

import requests

from cartography.intel.gitlab.environments import compute_env_variable_links
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
    assert ids == {f"{TEST_PROJECT_ID}:1", f"{TEST_PROJECT_ID}:2", f"{TEST_PROJECT_ID}:3"}


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
    """Build minimal env dicts: list of (id, name)."""
    return [{"id": eid, "name": name} for eid, name in specs]


def test_compute_env_variable_links_exact_match():
    envs = _envs([("e1", "production")])
    variables = _vars([("v1", "DB_URL", "production"), ("v2", "DB_URL", "staging")])
    links = compute_env_variable_links(envs, variables)
    assert links == [{"env_id": "e1", "variable_id": "v1"}]


def test_compute_env_variable_links_wildcard_match():
    envs = _envs([("e1", "production"), ("e2", "staging")])
    variables = _vars([("v1", "FEATURE_FLAG", "*")])
    links = compute_env_variable_links(envs, variables)
    # Wildcard variable applies to ALL envs
    assert {(link["env_id"], link["variable_id"]) for link in links} == {
        ("e1", "v1"),
        ("e2", "v1"),
    }


def test_compute_env_variable_links_mixes_exact_and_wildcard():
    envs = _envs([("e1", "production"), ("e2", "staging")])
    variables = _vars(
        [
            ("v1", "DB_URL", "production"),
            ("v2", "DB_URL", "staging"),
            ("v3", "FEATURE_FLAG", "*"),
        ]
    )
    links = compute_env_variable_links(envs, variables)
    pairs = {(link["env_id"], link["variable_id"]) for link in links}
    assert pairs == {("e1", "v1"), ("e2", "v2"), ("e1", "v3"), ("e2", "v3")}


def test_compute_env_variable_links_no_match():
    envs = _envs([("e1", "production")])
    variables = _vars([("v1", "X", "staging")])
    assert compute_env_variable_links(envs, variables) == []


def test_compute_env_variable_links_glob_pattern_does_not_match():
    """v1 has scope 'production/*' — GitLab expands it at runtime, but we don't."""
    envs = _envs([("e1", "production/web")])
    variables = _vars([("v1", "X", "production/*")])
    assert compute_env_variable_links(envs, variables) == []


def test_compute_env_variable_links_skips_envs_without_name():
    envs = [{"id": "e1"}, {"id": "e2", "name": "production"}]
    variables = _vars([("v1", "X", "*")])
    links = compute_env_variable_links(envs, variables)
    assert links == [{"env_id": "e2", "variable_id": "v1"}]


@patch("cartography.intel.gitlab.environments.get_paginated")
def test_get_environments_silences_403(mock_get_paginated):
    mock_get_paginated.side_effect = _http_error(403)
    assert get_environments(TEST_GITLAB_URL, "tok", TEST_PROJECT_ID) == []


@patch("cartography.intel.gitlab.environments.get_paginated")
def test_get_environments_propagates_500(mock_get_paginated):
    mock_get_paginated.side_effect = _http_error(500)
    try:
        get_environments(TEST_GITLAB_URL, "tok", TEST_PROJECT_ID)
        raise AssertionError("Expected HTTPError to propagate")
    except requests.exceptions.HTTPError:
        pass
