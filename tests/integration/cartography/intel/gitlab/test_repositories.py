from unittest.mock import patch

from cartography.intel.gitlab.repositories import _extract_groups_from_repositories
from cartography.intel.gitlab.repositories import _load_gitlab_groups
from cartography.intel.gitlab.repositories import _load_gitlab_repositories
from cartography.intel.gitlab.repositories import _load_programming_languages
from cartography.intel.gitlab.repositories import sync_gitlab_repositories
from tests.data.gitlab.repositories import GET_GITLAB_LANGUAGE_MAPPINGS
from tests.data.gitlab.repositories import GET_GITLAB_REPOSITORIES_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_GITLAB_URL = "https://gitlab.example.com"
TEST_GITLAB_TOKEN = "test_token_12345"


def _ensure_local_neo4j_has_test_data(neo4j_session):
    """Helper to load test data into Neo4j"""
    groups = _extract_groups_from_repositories(GET_GITLAB_REPOSITORIES_RESPONSE)
    _load_gitlab_groups(neo4j_session, groups, TEST_UPDATE_TAG)
    _load_gitlab_repositories(
        neo4j_session, GET_GITLAB_REPOSITORIES_RESPONSE, TEST_UPDATE_TAG
    )
    _load_programming_languages(
        neo4j_session, GET_GITLAB_LANGUAGE_MAPPINGS, TEST_UPDATE_TAG
    )


def test_extract_groups_from_repositories():
    """Test that groups are extracted correctly from repository data"""
    groups = _extract_groups_from_repositories(GET_GITLAB_REPOSITORIES_RESPONSE)

    # Should have 3 unique groups
    assert len(groups) == 3

    # Check that group IDs are present and include URL prefix
    group_ids = {group["id"] for group in groups}
    assert group_ids == {
        "https://gitlab.example.com/groups/10",
        "https://gitlab.example.com/groups/20",
        "https://gitlab.example.com/groups/30",
    }

    # Check that groups have required fields
    for group in groups:
        assert "id" in group
        assert "name" in group
        assert "path" in group
        assert "full_path" in group


def test_load_gitlab_repositories(neo4j_session):
    """Test that GitLab repositories are loaded correctly into Neo4j"""
    # Arrange & Act
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Assert - Check that repository nodes exist with rich metadata
    assert check_nodes(
        neo4j_session,
        "GitLabRepository",
        ["id", "name", "path_with_namespace", "visibility"],
    ) == {
        (
            "https://gitlab.example.com/projects/123",
            "awesome-project",
            "engineering/awesome-project",
            "private",
        ),
        (
            "https://gitlab.example.com/projects/456",
            "backend-service",
            "services/backend-service",
            "internal",
        ),
        (
            "https://gitlab.example.com/projects/789",
            "frontend-app",
            "apps/frontend-app",
            "public",
        ),
    }

    # Check URLs are populated
    result = neo4j_session.run(
        """
        MATCH (r:GitLabRepository)
        WHERE r.id = 'https://gitlab.example.com/projects/123'
        RETURN r.web_url as web_url,
               r.ssh_url_to_repo as ssh_url,
               r.http_url_to_repo as http_url
        """,
    )
    record = result.single()
    assert record["web_url"] == "https://gitlab.example.com/engineering/awesome-project"
    assert record["ssh_url"] == "git@gitlab.example.com:engineering/awesome-project.git"
    assert (
        record["http_url"]
        == "https://gitlab.example.com/engineering/awesome-project.git"
    )

    # Check stats are populated
    result = neo4j_session.run(
        """
        MATCH (r:GitLabRepository)
        WHERE r.id = 'https://gitlab.example.com/projects/789'
        RETURN r.star_count as stars,
               r.forks_count as forks,
               r.archived as archived
        """,
    )
    record = result.single()
    assert record["stars"] == 42
    assert record["forks"] == 8
    assert record["archived"] is False


def test_load_gitlab_groups(neo4j_session):
    """Test that GitLab groups are loaded correctly into Neo4j"""
    # Arrange & Act
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Assert - Check that group nodes exist
    assert check_nodes(
        neo4j_session,
        "GitLabGroup",
        ["id", "name", "path"],
    ) == {
        ("https://gitlab.example.com/groups/10", "Engineering", "engineering"),
        ("https://gitlab.example.com/groups/20", "Services", "services"),
        ("https://gitlab.example.com/groups/30", "Apps", "apps"),
    }


def test_group_to_repository_relationships(neo4j_session):
    """Test that OWNER relationships are created correctly"""
    # Arrange & Act
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Assert - Check OWNER relationships from Group to Repository
    assert check_rels(
        neo4j_session,
        "GitLabGroup",
        "id",
        "GitLabRepository",
        "id",
        "OWNER",
        rel_direction_right=True,
    ) == {
        (
            "https://gitlab.example.com/groups/10",
            "https://gitlab.example.com/projects/123",
        ),  # Engineering owns awesome-project
        (
            "https://gitlab.example.com/groups/20",
            "https://gitlab.example.com/projects/456",
        ),  # Services owns backend-service
        (
            "https://gitlab.example.com/groups/30",
            "https://gitlab.example.com/projects/789",
        ),  # Apps owns frontend-app
    }


def test_language_relationships(neo4j_session):
    """Test that LANGUAGE relationships are created correctly"""
    # Arrange & Act
    _ensure_local_neo4j_has_test_data(neo4j_session)

    # Assert - Check that ProgrammingLanguage nodes exist
    assert check_nodes(
        neo4j_session,
        "ProgrammingLanguage",
        ["name"],
    ) == {
        ("Python",),
        ("JavaScript",),
        ("Go",),
        ("Shell",),
        ("TypeScript",),
        ("CSS",),
        ("HTML",),
    }

    # Check LANGUAGE relationships from Repository to Language
    assert check_rels(
        neo4j_session,
        "GitLabRepository",
        "id",
        "ProgrammingLanguage",
        "name",
        "LANGUAGE",
        rel_direction_right=True,
    ) == {
        ("https://gitlab.example.com/projects/123", "Python"),
        ("https://gitlab.example.com/projects/123", "JavaScript"),
        ("https://gitlab.example.com/projects/456", "Go"),
        ("https://gitlab.example.com/projects/456", "Shell"),
        ("https://gitlab.example.com/projects/789", "TypeScript"),
        ("https://gitlab.example.com/projects/789", "CSS"),
        ("https://gitlab.example.com/projects/789", "HTML"),
    }

    # Check language percentage is stored on relationship
    result = neo4j_session.run(
        """
        MATCH (r:GitLabRepository {id: 'https://gitlab.example.com/projects/123'})-[rel:LANGUAGE]->(l:ProgrammingLanguage {name: 'Python'})
        RETURN rel.percentage as percentage
        """,
    )
    record = result.single()
    assert record["percentage"] == 65.5


@patch("cartography.intel.gitlab.repositories.get_gitlab_repositories")
@patch("cartography.intel.gitlab.repositories._get_repository_languages")
def test_sync_gitlab_repositories(mock_get_languages, mock_get_repos, neo4j_session):
    """Test the full sync_gitlab_repositories function"""
    # Arrange
    mock_get_repos.return_value = GET_GITLAB_REPOSITORIES_RESPONSE
    mock_get_languages.return_value = GET_GITLAB_LANGUAGE_MAPPINGS

    # Act
    sync_gitlab_repositories(
        neo4j_session,
        TEST_GITLAB_URL,
        TEST_GITLAB_TOKEN,
        TEST_UPDATE_TAG,
    )

    # Assert - Verify the mocks were called correctly
    mock_get_repos.assert_called_once_with(TEST_GITLAB_URL, TEST_GITLAB_TOKEN)
    mock_get_languages.assert_called_once()

    # Verify repositories were loaded
    assert check_nodes(
        neo4j_session,
        "GitLabRepository",
        ["id", "name"],
    ) == {
        ("https://gitlab.example.com/projects/123", "awesome-project"),
        ("https://gitlab.example.com/projects/456", "backend-service"),
        ("https://gitlab.example.com/projects/789", "frontend-app"),
    }

    # Verify groups were loaded
    assert check_nodes(
        neo4j_session,
        "GitLabGroup",
        ["name"],
    ) == {
        ("Engineering",),
        ("Services",),
        ("Apps",),
    }

    # Verify languages were loaded
    result = neo4j_session.run(
        """
        MATCH (l:ProgrammingLanguage)
        RETURN count(l) as count
        """,
    )
    record = result.single()
    assert record["count"] == 7
