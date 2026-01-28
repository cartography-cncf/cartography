"""Integration tests for GitLab users module."""

from unittest.mock import patch

from cartography.intel.gitlab.users import sync_gitlab_users
from tests.data.gitlab.users import GET_GITLAB_COMMITS
from tests.data.gitlab.users import GET_GITLAB_GROUP_MEMBERS
from tests.data.gitlab.users import TEST_ORG_URL
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = 100
TEST_GROUP_ID = 20
TEST_PROJECT_ID = 123


def _create_test_organization(neo4j_session):
    """Create test GitLabOrganization node."""
    neo4j_session.run(
        """
        MERGE (org:GitLabOrganization{id: $org_url})
        ON CREATE SET org.firstseen = timestamp()
        SET org.lastupdated = $update_tag,
            org.name = 'myorg'
        """,
        org_url=TEST_ORG_URL,
        update_tag=TEST_UPDATE_TAG,
    )


def _create_test_group(neo4j_session):
    """Create test GitLabGroup node."""
    neo4j_session.run(
        """
        MERGE (g:GitLabGroup{id: $group_url})
        ON CREATE SET g.firstseen = timestamp()
        SET g.lastupdated = $update_tag,
            g.name = 'Platform'
        """,
        group_url="https://gitlab.example.com/myorg/platform",
        update_tag=TEST_UPDATE_TAG,
    )


def _create_test_project(neo4j_session):
    """Create test GitLabProject node."""
    neo4j_session.run(
        """
        MERGE (p:GitLabProject{id: $project_url})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $update_tag,
            p.name = 'awesome-project'
        """,
        project_url="https://gitlab.example.com/myorg/awesome-project",
        update_tag=TEST_UPDATE_TAG,
    )


@patch("cartography.intel.gitlab.users.get_commits")
@patch("cartography.intel.gitlab.users.get_group_members")
@patch("cartography.intel.gitlab.users.get_organization")
def test_sync_gitlab_users(
    mock_get_organization,
    mock_get_group_members,
    mock_get_commits,
    neo4j_session,
):
    """Test end-to-end sync of GitLab users with group memberships and commit activity."""
    # Arrange - Clean up any existing users first
    neo4j_session.run("MATCH (u:GitLabUser) DETACH DELETE u")

    _create_test_organization(neo4j_session)
    _create_test_group(neo4j_session)
    _create_test_project(neo4j_session)

    # Mock API responses
    mock_get_organization.return_value = {"web_url": TEST_ORG_URL, "name": "myorg"}
    mock_get_group_members.return_value = GET_GITLAB_GROUP_MEMBERS
    mock_get_commits.return_value = GET_GITLAB_COMMITS

    test_groups = [
        {
            "id": TEST_GROUP_ID,
            "web_url": "https://gitlab.example.com/myorg/platform",
            "name": "Platform",
        }
    ]

    test_projects = [
        {
            "id": TEST_PROJECT_ID,
            "web_url": "https://gitlab.example.com/myorg/awesome-project",
            "name": "awesome-project",
        }
    ]

    # Act
    sync_gitlab_users(
        neo4j_session,
        "https://gitlab.example.com",
        "fake-token",
        TEST_UPDATE_TAG,
        {"ORGANIZATION_ID": TEST_ORG_ID},
        test_groups,
        test_projects,
    )

    # Assert - Check user node exists
    expected_users = {
        ("https://gitlab.example.com/alice", "alice", "Alice Smith"),
    }
    assert (
        check_nodes(neo4j_session, "GitLabUser", ["id", "username", "name"])
        == expected_users
    )

    # Assert - Check MEMBER_OF relationship to group
    expected_memberships = {
        (
            "https://gitlab.example.com/alice",
            "https://gitlab.example.com/myorg/platform",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabUser",
            "id",
            "GitLabGroup",
            "id",
            "MEMBER_OF",
        )
        == expected_memberships
    )

    # Assert - Check COMMITTED_TO relationship to project
    expected_commits = {
        (
            "https://gitlab.example.com/alice",
            "https://gitlab.example.com/myorg/awesome-project",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "GitLabUser",
            "id",
            "GitLabProject",
            "id",
            "COMMITTED_TO",
        )
        == expected_commits
    )
