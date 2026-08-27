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
    # Arrange - wipe state left by earlier tests in this module (the session
    # fixture is module-scoped), then seed repo1 pushed outside the lookback window.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
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

    # Assert - only repo2's commit relationship was written to the graph
    actual_rels = check_rels(
        neo4j_session,
        "GitHubUser",
        "id",
        "GitHubRepository",
        "id",
        "COMMITTED_TO",
        rel_direction_right=True,
    )
    assert actual_rels == {
        ("https://github.com/bob", "https://github.com/testorg/repo2"),
    }


@patch.object(
    cartography.intel.github.commits,
    "get_repo_commits",
)
def test_sync_github_commits_skip_stale_repos_touches_existing_rels(
    mock_get_commits, neo4j_session
):
    """
    Regression: a repo skipped by skip_stale_repos (pushedat outside the
    lookback window) whose existing COMMITTED_TO edge carries a prior
    update_tag must have that edge touched forward — not deleted by the
    org-scoped matchlink cleanup. `pushedat` is imprecise, so a stale-by-
    pushedat repo can still hold live commit edges; incremental sync must not
    silently delete them.
    """
    # Arrange - reset, seed nodes, and create a pre-existing COMMITTED_TO edge
    # on the to-be-skipped repo1 carrying an OLD update tag.
    old_update_tag = TEST_UPDATE_TAG - 1
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _ensure_test_users_exist(neo4j_session)
    _ensure_test_repos_exist(neo4j_session)
    neo4j_session.run(
        """
        MATCH (r1:GitHubRepository {id: "https://github.com/testorg/repo1"})
        SET r1.pushedat = "2000-01-01T00:00:00Z"
        WITH r1
        MATCH (u:GitHubUser {id: "https://github.com/alice"})
        MERGE (u)-[c:COMMITTED_TO]->(r1)
        SET c.lastupdated = $old_update_tag,
            c._sub_resource_label = "GitHubOrganization",
            c._sub_resource_id = "https://github.com/testorg"
        """,
        old_update_tag=old_update_tag,
    )

    def side_effect(token, api_url, organization, repo_name, since_date):
        return MOCK_COMMITS_BY_REPO.get(repo_name, [])

    mock_get_commits.side_effect = side_effect

    # Act - incremental sync with a NEW update tag; repo1 is skipped.
    cartography.intel.github.commits.sync_github_commits(
        neo4j_session,
        "fake-token",
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
        TEST_REPO_NAMES,
        TEST_UPDATE_TAG,
        skip_stale_repos=True,
    )

    # Assert - repo1 was skipped (no commits API call)...
    fetched_repos = {call.args[3] for call in mock_get_commits.call_args_list}
    assert fetched_repos == {"repo2"}

    # ...yet repo1's pre-existing edge survived AND was touched to the new tag,
    # instead of being deleted as stale by the cleanup.
    actual_rels = check_rels(
        neo4j_session,
        "GitHubUser",
        "id",
        "GitHubRepository",
        "id",
        "COMMITTED_TO",
        rel_direction_right=True,
    )
    assert (
        "https://github.com/alice",
        "https://github.com/testorg/repo1",
    ) in actual_rels

    touched = neo4j_session.run(
        """
        MATCH (:GitHubUser {id: "https://github.com/alice"})
              -[c:COMMITTED_TO]->
              (:GitHubRepository {id: "https://github.com/testorg/repo1"})
        RETURN c.lastupdated AS lastupdated
        """
    ).single()
    assert touched["lastupdated"] == TEST_UPDATE_TAG


@patch.object(
    cartography.intel.github.commits,
    "get_repo_commits",
)
def test_sync_github_commits_archived_repo_touches_existing_rels(
    mock_get_commits, neo4j_session
):
    """
    Regression (cubic PR #3200): an archived/disabled repo is excluded from
    `repo_names` before commits sync (filtered in start_github_ingestion), so it
    never reaches the stale-skip touch. Its existing COMMITTED_TO edge must still
    be touched forward, not deleted by the org-scoped matchlink cleanup.
    """
    # Arrange - repo1 is archived and NOT in the repo_names passed to sync, yet
    # it holds a pre-existing COMMITTED_TO edge carrying an OLD update tag.
    old_update_tag = TEST_UPDATE_TAG - 1
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _ensure_test_users_exist(neo4j_session)
    _ensure_test_repos_exist(neo4j_session)
    neo4j_session.run(
        """
        MATCH (r1:GitHubRepository {id: "https://github.com/testorg/repo1"})
        SET r1.archived = true, r1.disabled = false
        WITH r1
        MATCH (org:GitHubOrganization {id: "https://github.com/testorg"})
        MERGE (r1)-[:OWNER]->(org)
        WITH r1
        MATCH (u:GitHubUser {id: "https://github.com/alice"})
        MERGE (u)-[c:COMMITTED_TO]->(r1)
        SET c.lastupdated = $old_update_tag,
            c._sub_resource_label = "GitHubOrganization",
            c._sub_resource_id = "https://github.com/testorg"
        """,
        old_update_tag=old_update_tag,
    )

    def side_effect(token, api_url, organization, repo_name, since_date):
        return MOCK_COMMITS_BY_REPO.get(repo_name, [])

    mock_get_commits.side_effect = side_effect

    # Act - incremental sync; repo1 is archived so it is not in repo_names.
    cartography.intel.github.commits.sync_github_commits(
        neo4j_session,
        "fake-token",
        TEST_GITHUB_URL,
        TEST_GITHUB_ORG,
        ["repo2"],
        TEST_UPDATE_TAG,
        skip_stale_repos=True,
    )

    # Assert - repo1's commits were never fetched (excluded entirely)...
    fetched_repos = {call.args[3] for call in mock_get_commits.call_args_list}
    assert fetched_repos == {"repo2"}

    # ...yet repo1's pre-existing edge survived AND was touched to the new tag,
    # instead of being deleted as stale by the org-scoped cleanup.
    actual_rels = check_rels(
        neo4j_session,
        "GitHubUser",
        "id",
        "GitHubRepository",
        "id",
        "COMMITTED_TO",
        rel_direction_right=True,
    )
    assert (
        "https://github.com/alice",
        "https://github.com/testorg/repo1",
    ) in actual_rels

    touched = neo4j_session.run(
        """
        MATCH (:GitHubUser {id: "https://github.com/alice"})
              -[c:COMMITTED_TO]->
              (:GitHubRepository {id: "https://github.com/testorg/repo1"})
        RETURN c.lastupdated AS lastupdated
        """
    ).single()
    assert touched["lastupdated"] == TEST_UPDATE_TAG
