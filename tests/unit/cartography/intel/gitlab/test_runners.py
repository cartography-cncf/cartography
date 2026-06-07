"""Unit tests for GitLab runners module."""

from unittest.mock import Mock
from unittest.mock import patch

import requests

from cartography.intel.gitlab.runners import _list_runners_tolerant
from cartography.intel.gitlab.runners import get_runner_details
from cartography.intel.gitlab.runners import transform_runners
from tests.data.gitlab.runners import RUNNER_DETAILS
from tests.data.gitlab.runners import TEST_GITLAB_URL


def _http_error(status_code: int) -> requests.exceptions.HTTPError:
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    err = requests.exceptions.HTTPError(response=response)
    return err


def test_transform_runners_maps_all_fields():
    """transform_runners must propagate every security-relevant field."""
    raw = [RUNNER_DETAILS[3001]]
    result = transform_runners(raw, TEST_GITLAB_URL)

    assert len(result) == 1
    runner = result[0]
    assert runner["id"] == 3001
    assert runner["runner_type"] == "project_type"
    assert runner["run_untagged"] is True
    assert runner["locked"] is False
    assert runner["access_level"] == "not_protected"
    assert runner["tag_list"] == []
    assert runner["architecture"] == "arm64"
    assert runner["platform"] == "linux"
    assert runner["maximum_timeout"] is None
    assert runner["gitlab_url"] == TEST_GITLAB_URL


def test_transform_runners_preserves_tag_list():
    """tag_list is stored as an array, not stringified."""
    raw = [RUNNER_DETAILS[1001], RUNNER_DETAILS[2001]]
    result = transform_runners(raw, TEST_GITLAB_URL)

    assert result[0]["tag_list"] == ["shared", "linux"]
    assert result[1]["tag_list"] == ["group-only"]


def test_transform_runners_handles_missing_tag_list():
    """A runner without tag_list yields an empty array, not None."""
    raw = [{"id": 9, "runner_type": "instance_type"}]
    result = transform_runners(raw, TEST_GITLAB_URL)
    assert result[0]["tag_list"] == []


def test_transform_runners_skips_none_entries():
    """None entries (e.g. from skipped detail fetches) are dropped."""
    raw = [None, RUNNER_DETAILS[1001], None]
    result = transform_runners(raw, TEST_GITLAB_URL)
    assert len(result) == 1
    assert result[0]["id"] == 1001


def test_transform_runners_marks_protected_runner():
    """A locked, ref_protected, untagged-disallowed runner is the safe baseline."""
    raw = [RUNNER_DETAILS[2001]]
    result = transform_runners(raw, TEST_GITLAB_URL)
    runner = result[0]
    assert runner["locked"] is True
    assert runner["access_level"] == "ref_protected"
    assert runner["run_untagged"] is False


@patch("cartography.intel.gitlab.runners.get_paginated")
def test_list_runners_tolerant_returns_none_on_403(mock_get_paginated):
    """A 403 returns ``None`` (sentinel — caller skips load+cleanup)."""
    mock_get_paginated.side_effect = _http_error(403)
    result = _list_runners_tolerant(
        TEST_GITLAB_URL, "tok", "/api/v4/runners/all", "instance runners"
    )
    assert result is None


@patch("cartography.intel.gitlab.runners.get_paginated")
def test_list_runners_tolerant_propagates_other_errors(mock_get_paginated):
    """Any non-403 HTTPError must propagate."""
    mock_get_paginated.side_effect = _http_error(500)
    try:
        _list_runners_tolerant(
            TEST_GITLAB_URL, "tok", "/api/v4/runners/all", "instance runners"
        )
        raise AssertionError("Expected HTTPError to propagate")
    except requests.exceptions.HTTPError:
        pass


@patch("cartography.intel.gitlab.runners.get_single")
def test_get_runner_details_returns_none_on_403(mock_get_single):
    mock_get_single.side_effect = _http_error(403)
    assert get_runner_details(TEST_GITLAB_URL, "tok", 1) is None


@patch("cartography.intel.gitlab.runners.get_single")
def test_get_runner_details_returns_none_on_404(mock_get_single):
    mock_get_single.side_effect = _http_error(404)
    assert get_runner_details(TEST_GITLAB_URL, "tok", 1) is None


@patch("cartography.intel.gitlab.runners.get_single")
def test_get_runner_details_propagates_500(mock_get_single):
    mock_get_single.side_effect = _http_error(500)
    try:
        get_runner_details(TEST_GITLAB_URL, "tok", 1)
        raise AssertionError("Expected HTTPError to propagate")
    except requests.exceptions.HTTPError:
        pass
