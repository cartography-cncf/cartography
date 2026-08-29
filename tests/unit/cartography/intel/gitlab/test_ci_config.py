"""Unit tests for the GitLab CI config orchestration module."""

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
        project_variables=_project_variables(),
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


def test_transform_ci_config_referenced_variable_ids_drives_other_rel():
    """Referenced variable IDs are emitted for the one_to_many other_relationship."""
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES)
    record = transform_ci_config(
        parsed,
        TEST_PROJECT_ID,
        TEST_GITLAB_URL,
        is_merged=True,
        file_path=FILE_PATH,
        project_variables=_project_variables(),
    )
    # DATABASE_URL and DEPLOY_TOKEN match referenced keys; UNUSED does not.
    assert set(record["referenced_variable_ids"]) == {
        "project:123:DATABASE_URL:production",
        "project:123:DEPLOY_TOKEN:*",
    }


def test_transform_ci_config_no_referenced_variables_yields_empty_ids():
    parsed = parse_ci_config("")  # empty pipeline → no references
    record = transform_ci_config(
        parsed,
        TEST_PROJECT_ID,
        TEST_GITLAB_URL,
        is_merged=False,
        file_path=FILE_PATH,
        project_variables=_project_variables(),
    )
    assert record["referenced_variable_ids"] == []


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
