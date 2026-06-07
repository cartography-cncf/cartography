"""Unit tests for GitLab CI/CD variables module."""

from unittest.mock import Mock
from unittest.mock import patch

import requests

from cartography.intel.gitlab.ci_variables import _make_variable_id
from cartography.intel.gitlab.ci_variables import get_group_variables
from cartography.intel.gitlab.ci_variables import get_project_variables
from cartography.intel.gitlab.ci_variables import transform_variables
from tests.data.gitlab.ci_variables import GET_GROUP_VARIABLES_RESPONSE
from tests.data.gitlab.ci_variables import GET_PROJECT_VARIABLES_RESPONSE
from tests.data.gitlab.ci_variables import TEST_GITLAB_URL
from tests.data.gitlab.ci_variables import TEST_GROUP_ID
from tests.data.gitlab.ci_variables import TEST_PROJECT_ID


def _http_error(status_code: int) -> requests.exceptions.HTTPError:
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    return requests.exceptions.HTTPError(response=response)


def test_make_variable_id_includes_environment_scope():
    """Two vars with same key but different env_scope must have different IDs."""
    a = _make_variable_id("project", 123, "DATABASE_URL", "production")
    b = _make_variable_id("project", 123, "DATABASE_URL", "staging")
    assert a != b
    assert "production" in a
    assert "staging" in b


def test_make_variable_id_distinguishes_scope_types():
    """A var with same key in group vs project must have different IDs."""
    a = _make_variable_id("group", 42, "TOKEN", "*")
    b = _make_variable_id("project", 42, "TOKEN", "*")
    assert a != b


def test_transform_variables_drops_value():
    """The variable's value must NEVER appear in the transformed output."""
    transformed = transform_variables(
        GET_GROUP_VARIABLES_RESPONSE, "group", TEST_GROUP_ID, TEST_GITLAB_URL
    )
    for variable in transformed:
        assert "value" not in variable


def test_transform_variables_propagates_protected():
    transformed = transform_variables(
        GET_GROUP_VARIABLES_RESPONSE, "group", TEST_GROUP_ID, TEST_GITLAB_URL
    )
    by_key = {v["key"]: v for v in transformed}
    assert by_key["DEPLOY_TOKEN"]["protected"] is True
    assert by_key["GROUP_OPEN_VAR"]["protected"] is False


def test_transform_variables_default_environment_scope_is_wildcard():
    """A variable without `environment_scope` in the API response defaults to '*'."""
    transformed = transform_variables(
        GET_PROJECT_VARIABLES_RESPONSE, "project", TEST_PROJECT_ID, TEST_GITLAB_URL
    )
    config_file = next(v for v in transformed if v["key"] == "CONFIG_FILE")
    assert config_file["environment_scope"] == "*"


def test_transform_variables_handles_same_key_different_env_scopes():
    """Two DATABASE_URL variables (production / staging) must both survive."""
    transformed = transform_variables(
        GET_PROJECT_VARIABLES_RESPONSE, "project", TEST_PROJECT_ID, TEST_GITLAB_URL
    )
    db_urls = [v for v in transformed if v["key"] == "DATABASE_URL"]
    assert len(db_urls) == 2
    ids = {v["id"] for v in db_urls}
    assert len(ids) == 2  # distinct IDs
    scopes = {v["environment_scope"] for v in db_urls}
    assert scopes == {"production", "staging"}


def test_transform_variables_skips_entries_without_key():
    """A malformed entry without a key is dropped."""
    transformed = transform_variables(
        [{"value": "x"}], "project", TEST_PROJECT_ID, TEST_GITLAB_URL
    )
    assert transformed == []


def test_transform_variables_id_includes_scope_id():
    transformed = transform_variables(
        [{"key": "K", "environment_scope": "*"}],
        "project",
        TEST_PROJECT_ID,
        TEST_GITLAB_URL,
    )
    assert transformed[0]["id"] == f"project:{TEST_PROJECT_ID}:K:*"


@patch("cartography.intel.gitlab.ci_variables.get_paginated")
def test_get_group_variables_returns_none_on_403(mock_get_paginated):
    """Sentinel ``None`` so the caller can skip BOTH load AND cleanup."""
    mock_get_paginated.side_effect = _http_error(403)
    assert get_group_variables(TEST_GITLAB_URL, "tok", TEST_GROUP_ID) is None


@patch("cartography.intel.gitlab.ci_variables.get_paginated")
def test_get_project_variables_returns_none_on_403(mock_get_paginated):
    mock_get_paginated.side_effect = _http_error(403)
    assert get_project_variables(TEST_GITLAB_URL, "tok", TEST_PROJECT_ID) is None


@patch("cartography.intel.gitlab.ci_variables.get_paginated")
def test_get_group_variables_propagates_500(mock_get_paginated):
    mock_get_paginated.side_effect = _http_error(500)
    try:
        get_group_variables(TEST_GITLAB_URL, "tok", TEST_GROUP_ID)
        raise AssertionError("Expected HTTPError to propagate")
    except requests.exceptions.HTTPError:
        pass
