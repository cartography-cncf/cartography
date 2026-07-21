from unittest.mock import patch

import cartography.intel.github.commits
from tests.data.github.commits import MOCK_COMMITS_BY_REPO
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_GITHUB_URL = "https://fake.github.net/graphql/"
TEST_GITHUB_ORG = "testorg"
TEST_REPO_NAMES = ["repo1", "repo2"]


def _ensure_test_users_exist(neo4j_session):
    """Ensure test GitHubUser nodes exist for relationship testing."""
    neo4j_session.run(
        """
        MERGE (u1:GitHubUser {id: "https://github.com/alice"})
        SET u1.username = "alice", u1.lastupdated = $update_tag

        MERGE (u2:GitHubUser {id: "https://github.com/bob"})
        SET u2.username = "bob", u2.lastupdated = $update_tag
    """,
        update_tag=TEST_UPDATE_TAG,
    )


def _ensure_test_repos_exist(neo4j_session):
    """Ensure test GitHubRepository nodes exist for relationship testing."""
    neo4j_session.run(
        """
        MERGE (r1:GitHubRepository {id: "https://github.com/testorg/repo1"})
        SET r1.name = "repo1", r1.fullname = "testorg/repo1", r1.lastupdated = $update_tag

        MERGE (r2:GitHubRepository {id: "https://github.com/testorg/repo2"})
        SET r2.name = "repo2", r2.fullname = "testorg/repo2", r2.lastupdated = $update_tag

        MERGE (org:GitHubOrganization {id: "https://github.com/testorg"})
        SET org.username = "testorg", org.lastupdated = $update_tag
    """,
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.github.commits,
    "get_repo_commits",
)
def test_sync_github_commits(mock_get_commits, neo4j_session):
    """
    Test that GitHub commit relationships sync correctly and create proper MatchLink relationships.
    """
    # Arrange - Ensure prerequisite nodes exist
    _ensure_test_users_exist(neo4j_session)
    _ensure_test_repos_exist(neo4j_session)

    # Mock the get_repo_commits function to return different data for each repo
    def side_effect(token, api_url, organization, repo_name, since_date):
        return MOCK_COMMITS_BY_REPO.get(repo_name, [])

    mock_get_commits.side_effect = side_effect

    # Act - Sync commit relationships
    cartography.intel.github.commits.sync_github_commits(
        neo4j_session,
        "fake-token",
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
        TEST_REPO_NAMES,
        TEST_UPDATE_TAG,
    )

    # Assert - Verify relationships were created using check_rels
    expected_rels = {
        ("https://github.com/alice", "https://github.com/testorg/repo1"),
        ("https://github.com/bob", "https://github.com/testorg/repo2"),
    }

    actual_rels = check_rels(
        neo4j_session,
        "GitHubUser",
        "id",
        "GitHubRepository",
        "id",
        "COMMITTED_TO",
        rel_direction_right=True,
    )

    assert actual_rels == expected_rels

    # Verify nodes exist using check_nodes
    expected_users = {
        ("https://github.com/alice",),
        ("https://github.com/bob",),
    }
    actual_users = check_nodes(neo4j_session, "GitHubUser", ["id"])
    assert expected_users.issubset(actual_users)

    expected_repos = {
        ("https://github.com/testorg/repo1",),
        ("https://github.com/testorg/repo2",),
    }
    actual_repos = check_nodes(neo4j_session, "GitHubRepository", ["id"])
    assert expected_repos.issubset(actual_repos)


@patch.object(
    cartography.intel.github.commits,
    "get_repo_commits",
)
def test_sync_github_commits_skip_stale_repos(mock_get_commits, neo4j_session):
    """
    Test that when skip_stale_repos is enabled, repos with no push within the
    lookback window are skipped entirely (no commits API call), while repos
    with no known pushedat (never seen by a repos sync) are still processed.
    """
    # Arrange - repo1 was pushed long ago (outside the lookback window), repo2 recently.
    _ensure_test_users_exist(neo4j_session)
    _ensure_test_repos_exist(neo4j_session)
    neo4j_session.run(
        """
        MATCH (r1:GitHubRepository {id: "https://github.com/testorg/repo1"})
        SET r1.pushedat = "2000-01-01T00:00:00Z"
        """,
    )
    # repo2 has no pushedat set at all (simulates a repo the repos-sync hasn't
    # recorded pushedat for yet) — should never be skipped.

    def side_effect(token, api_url, organization, repo_name, since_date):
        return MOCK_COMMITS_BY_REPO.get(repo_name, [])

    mock_get_commits.side_effect = side_effect

    # Act
    cartography.intel.github.commits.sync_github_commits(
        neo4j_session,
        "fake-token",
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
        TEST_REPO_NAMES,
        TEST_UPDATE_TAG,
        skip_stale_repos=True,
    )

    # Assert - only repo2 (no pushedat on record) had its commits fetched
    fetched_repos = {call.args[3] for call in mock_get_commits.call_args_list}
    assert fetched_repos == {"repo2"}
