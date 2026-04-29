"""Unit tests for the GitLab CI config orchestration module."""

from cartography.intel.gitlab.ci_config import compute_config_variable_links
from cartography.intel.gitlab.ci_config import transform_ci_config
from cartography.intel.gitlab.ci_config import transform_ci_includes
from cartography.intel.gitlab.ci_config_parser import parse_ci_config
from tests.data.gitlab.ci_configs import PIPELINE_WITH_MIXED_INCLUDES
from tests.data.gitlab.ci_configs import TEST_GITLAB_URL
from tests.data.gitlab.ci_configs import TEST_PROJECT_ID

FILE_PATH = ".gitlab-ci.yml"


def _project_variables():
    return [
        {
            "id": "project:123:DATABASE_URL:production",
            "key": "DATABASE_URL",
            "protected": True,
            "environment_scope": "production",
        },
        {
            "id": "project:123:DEPLOY_TOKEN:*",
            "key": "DEPLOY_TOKEN",
            "protected": True,
            "environment_scope": "*",
        },
        {
            "id": "project:123:UNUSED:*",
            "key": "UNUSED",
            "protected": False,
            "environment_scope": "*",
        },
    ]


def test_transform_ci_config_records_referenced_protected_variables():
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES)
    record = transform_ci_config(
        parsed,
        TEST_PROJECT_ID,
        TEST_GITLAB_URL,
        is_merged=True,
        file_path=FILE_PATH,
        project_protected_variable_keys={"DATABASE_URL", "DEPLOY_TOKEN"},
    )
    assert record["id"] == f"{TEST_PROJECT_ID}:{FILE_PATH}"
    assert record["is_merged"] is True
    # Both DATABASE_URL and DEPLOY_TOKEN are referenced AND protected.
    assert set(record["referenced_protected_variables"]) == {
        "DATABASE_URL",
        "DEPLOY_TOKEN",
    }
    # include_count and has_includes coherent with parsed.
    assert record["has_includes"] is True
    assert record["include_count"] == len(parsed.includes)


def test_transform_ci_includes_records_one_per_include():
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES)
    records = transform_ci_includes(parsed, TEST_PROJECT_ID, TEST_GITLAB_URL, FILE_PATH)
    assert len(records) == len(parsed.includes)
    # Each record links to the parent config_id.
    expected_config_id = f"{TEST_PROJECT_ID}:{FILE_PATH}"
    assert all(r["config_id"] == expected_config_id for r in records)


def test_transform_ci_includes_id_distinguishes_pinned_vs_unpinned_project():
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES)
    records = transform_ci_includes(parsed, TEST_PROJECT_ID, TEST_GITLAB_URL, FILE_PATH)
    project_records = [r for r in records if r["include_type"] == "project"]
    ids = {r["id"] for r in project_records}
    assert len(ids) == 2  # pinned and unpinned have distinct IDs


def test_compute_config_variable_links_matches_referenced_keys():
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES)
    links = compute_config_variable_links(
        parsed, _project_variables(), TEST_PROJECT_ID, FILE_PATH
    )
    variable_ids = {link["variable_id"] for link in links}
    # DATABASE_URL and DEPLOY_TOKEN are referenced; UNUSED is not.
    assert variable_ids == {
        "project:123:DATABASE_URL:production",
        "project:123:DEPLOY_TOKEN:*",
    }


def test_compute_config_variable_links_no_referenced_returns_empty():
    parsed = parse_ci_config("")
    assert (
        compute_config_variable_links(
            parsed, _project_variables(), TEST_PROJECT_ID, FILE_PATH
        )
        == []
    )
