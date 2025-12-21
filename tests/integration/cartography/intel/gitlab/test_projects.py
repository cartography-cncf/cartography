from unittest.mock import patch

from cartography.intel.gitlab.projects import _extract_repo_name_from_url
from cartography.intel.gitlab.projects import _load_gitlab_projects
from cartography.intel.gitlab.projects import _load_gitlab_repositories
from cartography.intel.gitlab.projects import _transform_gitlab_projects
from cartography.intel.gitlab.projects import sync_gitlab_projects
from tests.data.gitlab.projects import GET_GITLAB_PROJECTS_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_GITLAB_URL = "https://gitlab.example.com"
TEST_GITLAB_TOKEN = "test_token_12345"


def _ensure_local_neo4j_has_test_data(neo4j_session):
    """Helper to load test data into Neo4j"""
    projects_data, repositories_data = _transform_gitlab_projects(
        GET_GITLAB_PROJECTS_RESPONSE
    )
    _load_gitlab_repositories(neo4j_session, repositories_data, TEST_UPDATE_TAG)
    _load_gitlab_projects(neo4j_session, projects_data, TEST_UPDATE_TAG)


def test_extract_repo_name_from_url():
    """Test that repository names are extracted correctly from URLs"""
    assert (
        _extract_repo_name_from_url("https://gitlab.example.com/team/awesome-project")
        == "team/awesome-project"
    )
    assert (
        _extract_repo_name_from_url("https://gitlab.example.com/group/subgroup/repo")
        == "group/subgroup/repo"
    )
    assert (
        _extract_repo_name_from_url(
            "https://gitlab.example.com/user%20name/project%20name"
        )
        == "user name/project name"
    )


def test_transform_gitlab_projects():
    """Test that project data is transformed correctly"""
    projects_data, repositories_data = _transform_gitlab_projects(
        GET_GITLAB_PROJECTS_RESPONSE
    )

    # Check that we have 4 projects and 4 repositories
    assert len(projects_data) == 4
    assert len(repositories_data) == 4

    # Check that all projects have repository_id field
    for project in projects_data:
        assert "repository_id" in project
        assert project["repository_id"].startswith("gitlab_")

    # Check that repository IDs are unique
    repo_ids = [repo["id"] for repo in repositories_data]
    assert len(repo_ids) == len(set(repo_ids))


def test_load_gitlab_projects(neo4j_session):
    """Test that GitLab projects are loaded correctly into Neo4j"""
    # Arrange & Act
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Assert - Check that project nodes exist
    assert check_nodes(
        neo4j_session,
        "GitLabProject",
        ["id", "name", "url"],
    ) == {
        (123, "awesome-project", "https://gitlab.example.com/team/awesome-project"),
        (456, "backend-service", "https://gitlab.example.com/services/backend-service"),
        (789, "frontend-app", "https://gitlab.example.com/apps/frontend-app"),
        (101112, "data-pipeline", "https://gitlab.example.com/data/data-pipeline"),
    }


def test_load_gitlab_repositories(neo4j_session):
    """Test that GitLab repositories are loaded correctly into Neo4j"""
    # Arrange & Act
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Assert - Check that repository nodes exist
    assert check_nodes(
        neo4j_session,
        "GitLabRepository",
        ["id", "name"],
    ) == {
        ("gitlab_team/awesome-project", "team/awesome-project"),
        ("gitlab_services/backend-service", "services/backend-service"),
        ("gitlab_apps/frontend-app", "apps/frontend-app"),
        ("gitlab_data/data-pipeline", "data/data-pipeline"),
    }


def test_project_to_repository_relationships(neo4j_session):
    """Test that SOURCE_CODE relationships are created correctly"""
    # Arrange & Act
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Assert - Check SOURCE_CODE relationships
    assert check_rels(
        neo4j_session,
        "GitLabProject",
        "id",
        "GitLabRepository",
        "id",
        "SOURCE_CODE",
        rel_direction_right=True,
    ) == {
        (123, "gitlab_team/awesome-project"),
        (456, "gitlab_services/backend-service"),
        (789, "gitlab_apps/frontend-app"),
        (101112, "gitlab_data/data-pipeline"),
    }


@patch("cartography.intel.gitlab.projects.get_gitlab_projects")
def test_sync_gitlab_projects(mock_get_gitlab_projects, neo4j_session):
    """Test the full sync_gitlab_projects function"""
    # Arrange
    mock_get_gitlab_projects.return_value = GET_GITLAB_PROJECTS_RESPONSE

    # Act
    sync_gitlab_projects(
        neo4j_session,
        TEST_GITLAB_URL,
        TEST_GITLAB_TOKEN,
        TEST_UPDATE_TAG,
    )

    # Assert - Verify the mock was called correctly
    mock_get_gitlab_projects.assert_called_once_with(
        TEST_GITLAB_URL,
        TEST_GITLAB_TOKEN,
    )

    # Verify data was loaded correctly
    assert check_nodes(
        neo4j_session,
        "GitLabProject",
        ["id", "name"],
    ) == {
        (123, "awesome-project"),
        (456, "backend-service"),
        (789, "frontend-app"),
        (101112, "data-pipeline"),
    }

    # Verify repositories were created
    assert check_nodes(
        neo4j_session,
        "GitLabRepository",
        ["name"],
    ) == {
        ("team/awesome-project",),
        ("services/backend-service",),
        ("apps/frontend-app",),
        ("data/data-pipeline",),
    }
