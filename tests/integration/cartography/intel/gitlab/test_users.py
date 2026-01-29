"""Integration tests for GitLab users module."""

from unittest.mock import patch

from cartography.intel.gitlab.users import sync_gitlab_users
from tests.data.gitlab.users import GET_GITLAB_COMMITS
from tests.data.gitlab.users import GET_GITLAB_GROUP_MEMBERS
from tests.data.gitlab.users import GET_GITLAB_ORG_MEMBERS
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
    # Use side_effect to return different data for org vs group member calls
    # First call: org members (Alice + Bob), Second call: group members (Alice only)
    mock_get_organization.return_value = {"web_url": TEST_ORG_URL, "name": "myorg"}
    mock_get_group_members.side_effect = [
        GET_GITLAB_ORG_MEMBERS,  # First call: organization members
        GET_GITLAB_GROUP_MEMBERS,  # Second call: Platform group members
    ]
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
        commits_since_days=90,
    )

    # Assert - Check both user nodes exist
    expected_users = {
        ("https://gitlab.example.com/alice", "alice", "Alice Smith"),
        ("https://gitlab.example.com/bob", "bob", "Bob Jones"),
    }
    assert (
        check_nodes(neo4j_session, "GitLabUser", ["id", "username", "name"])
        == expected_users
    )

    # Assert - Check MEMBER_OF relationship to group
    # Only Alice is in the Platform group, Bob is org-only
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
    # Both Alice and Bob have commits
    expected_commits = {
        (
            "https://gitlab.example.com/alice",
            "https://gitlab.example.com/myorg/awesome-project",
        ),
        (
            "https://gitlab.example.com/bob",
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

    # Assert - Check COMMITTED_TO relationship properties for Alice (2 commits)
    alice_result = neo4j_session.run(
        """
        MATCH (u:GitLabUser)-[r:COMMITTED_TO]->(p:GitLabProject)
        WHERE u.id = $user_id AND p.id = $project_id
        RETURN r.commit_count AS commit_count,
               r.first_commit_date AS first_commit_date,
               r.last_commit_date AS last_commit_date
        """,
        user_id="https://gitlab.example.com/alice",
        project_id="https://gitlab.example.com/myorg/awesome-project",
    ).single()

    assert alice_result is not None, "Alice's COMMITTED_TO relationship should exist"
    assert alice_result["commit_count"] == 2, "Alice should have 2 commits"
    assert (
        alice_result["first_commit_date"] == "2024-12-01T10:00:00Z"
    ), "Alice's first commit date should match earliest commit"
    assert (
        alice_result["last_commit_date"] == "2024-12-05T14:30:00Z"
    ), "Alice's last commit date should match latest commit"

    # Assert - Check COMMITTED_TO relationship properties for Bob (1 commit)
    bob_result = neo4j_session.run(
        """
        MATCH (u:GitLabUser)-[r:COMMITTED_TO]->(p:GitLabProject)
        WHERE u.id = $user_id AND p.id = $project_id
        RETURN r.commit_count AS commit_count,
               r.first_commit_date AS first_commit_date,
               r.last_commit_date AS last_commit_date
        """,
        user_id="https://gitlab.example.com/bob",
        project_id="https://gitlab.example.com/myorg/awesome-project",
    ).single()

    assert bob_result is not None, "Bob's COMMITTED_TO relationship should exist"
    assert bob_result["commit_count"] == 1, "Bob should have 1 commit"
    assert (
        bob_result["first_commit_date"] == "2024-12-03T09:15:00Z"
    ), "Bob's first commit date should match his only commit"
    assert (
        bob_result["last_commit_date"] == "2024-12-03T09:15:00Z"
    ), "Bob's last commit date should match his only commit"
