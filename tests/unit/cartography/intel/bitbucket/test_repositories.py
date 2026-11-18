from cartography.intel.bitbucket.repositories import transform_repositories
from tests.data.bitbucket.repositories import MOCK_REPOSITORIES


def test_transform_repositories_with_project():
    result = transform_repositories(MOCK_REPOSITORIES["values"])
    with_project = next(r for r in result if r["id"] == "repo-uuid-1")

    assert with_project["project_key"] == "PROJ"
    assert with_project["project_id"] == "project-uuid-1"
    assert with_project["clone_https"] == (
        "https://bitbucket.org/my-workspace/repo-with-project.git"
    )
    assert with_project["clone_ssh"] == (
        "git@bitbucket.org:my-workspace/repo-with-project.git"
    )
    assert with_project["mainbranch_name"] == "main"


def test_transform_repositories_without_project_omits_project_fields():
    result = transform_repositories(MOCK_REPOSITORIES["values"])
    without_project = next(r for r in result if r["id"] == "repo-uuid-2")

    # No project on the raw repo means no project_key/project_id keys at all,
    # so the CONTAINS relationship is skipped for this record.
    assert "project_key" not in without_project
    assert "project_id" not in without_project


def test_transform_repositories_handles_null_mainbranch():
    repo = {**MOCK_REPOSITORIES["values"][0], "mainbranch": None}

    result = transform_repositories([repo])

    assert result[0]["mainbranch_name"] is None
