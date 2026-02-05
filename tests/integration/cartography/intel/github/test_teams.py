from unittest.mock import patch

import cartography.intel.github.teams
from cartography.intel.github.teams import sync_github_teams
from tests.data.github.teams import GH_TEAM_CHILD_TEAM
from tests.data.github.teams import GH_TEAM_DATA
from tests.data.github.teams import GH_TEAM_REPOS
from tests.data.github.teams import GH_TEAM_USERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://fake.github.net/graphql/"
FAKE_API_KEY = "asdf"


def _ensure_prerequisite_data_exists(neo4j_session):
    """
    Create prerequisite GitHubOrganization, GitHubRepository, and GitHubUser nodes
    needed for teams test.
    """
    # Create organization
    neo4j_session.run(
        """
        MERGE (org:GitHubOrganization{id: "https://github.com/simpsoncorp"})
        SET org.username = "simpsoncorp"
        """,
    )

    # Create repositories
    neo4j_session.run(
        """
        MERGE (repo1:GitHubRepository{id: "https://github.com/simpsoncorp/sample_repo"})
        SET repo1.name = "sample_repo"

        MERGE (repo2:GitHubRepository{id: "https://github.com/simpsoncorp/SampleRepo2"})
        SET repo2.name = "SampleRepo2"

        MERGE (repo3:GitHubRepository{id: "https://github.com/cartography-cncf/cartography"})
        SET repo3.name = "cartography"
        """,
    )

    # Create users
    neo4j_session.run(
        """
        MERGE (u1:GitHubUser{id: "https://github.com/hjsimpson"})
        SET u1.username = "hjsimpson"

        MERGE (u2:GitHubUser{id: "https://github.com/lmsimpson"})
        SET u2.username = "lmsimpson"

        MERGE (u3:GitHubUser{id: "https://github.com/mbsimpson"})
        SET u3.username = "mbsimpson"
        """,
    )


@patch.object(
    cartography.intel.github.teams,
    "_get_child_teams",
    return_value=GH_TEAM_CHILD_TEAM,
)
@patch.object(
    cartography.intel.github.teams,
    "_get_team_users",
    return_value=GH_TEAM_USERS,
)
@patch.object(
    cartography.intel.github.teams,
    "_get_team_repos",
    return_value=GH_TEAM_REPOS,
)
@patch.object(cartography.intel.github.teams, "get_teams", return_value=GH_TEAM_DATA)
def test_sync_github_teams(
    mock_teams,
    mock_team_repos,
    mock_team_users,
    mock_child_teams,
    neo4j_session,
):
    """
    Test that GitHub teams sync correctly with proper nodes and relationships.
    """
    # Arrange - Create prerequisite data
    _ensure_prerequisite_data_exists(neo4j_session)
    # Add another org to make sure we don't attach a node to the wrong org
    neo4j_session.run(
        """
        MERGE (g:GitHubOrganization{id: "this should have no attachments"})
    """,
    )

    # Act
    sync_github_teams(
        neo4j_session,
        TEST_JOB_PARAMS,
        FAKE_API_KEY,
        TEST_GITHUB_URL,
        "SimpsonCorp",
    )

    # Assert - Verify GitHubTeam nodes were created
    assert check_nodes(neo4j_session, "GitHubTeam", ["id", "url", "name"]) == {
        (
            "https://github.com/orgs/simpsoncorp/teams/team-a",
            "https://github.com/orgs/simpsoncorp/teams/team-a",
            "team-a",
        ),
        (
            "https://github.com/orgs/simpsoncorp/teams/team-b",
            "https://github.com/orgs/simpsoncorp/teams/team-b",
            "team-b",
        ),
        (
            "https://github.com/orgs/simpsoncorp/teams/team-c",
            "https://github.com/orgs/simpsoncorp/teams/team-c",
            "team-c",
        ),
        (
            "https://github.com/orgs/simpsoncorp/teams/team-d",
            "https://github.com/orgs/simpsoncorp/teams/team-d",
            "team-d",
        ),
        (
            "https://github.com/orgs/simpsoncorp/teams/team-e",
            "https://github.com/orgs/simpsoncorp/teams/team-e",
            "team-e",
        ),
    }

    # Assert - Verify RESOURCE relationships to organization
    assert check_rels(
        neo4j_session,
        "GitHubTeam",
        "id",
        "GitHubOrganization",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        (
            "https://github.com/orgs/simpsoncorp/teams/team-a",
            "https://github.com/simpsoncorp",
        ),
        (
            "https://github.com/orgs/simpsoncorp/teams/team-b",
            "https://github.com/simpsoncorp",
        ),
        (
            "https://github.com/orgs/simpsoncorp/teams/team-c",
            "https://github.com/simpsoncorp",
        ),
        (
            "https://github.com/orgs/simpsoncorp/teams/team-d",
            "https://github.com/simpsoncorp",
        ),
        (
            "https://github.com/orgs/simpsoncorp/teams/team-e",
            "https://github.com/simpsoncorp",
        ),
    }

    # Assert - Verify ADMIN relationships to repositories
    assert check_rels(
        neo4j_session,
        "GitHubTeam",
        "id",
        "GitHubRepository",
        "id",
        "ADMIN",
        rel_direction_right=True,
    ) == {
        (
            "https://github.com/orgs/simpsoncorp/teams/team-b",
            "https://github.com/simpsoncorp/sample_repo",
        ),
    }

    # Assert - Verify WRITE relationships to repositories
    assert check_rels(
        neo4j_session,
        "GitHubTeam",
        "id",
        "GitHubRepository",
        "id",
        "WRITE",
        rel_direction_right=True,
    ) == {
        (
            "https://github.com/orgs/simpsoncorp/teams/team-b",
            "https://github.com/simpsoncorp/SampleRepo2",
        ),
    }

    # Assert - Verify READ relationships to repositories
    assert check_rels(
        neo4j_session,
        "GitHubTeam",
        "id",
        "GitHubRepository",
        "id",
        "READ",
        rel_direction_right=True,
    ) == {
        (
            "https://github.com/orgs/simpsoncorp/teams/team-b",
            "https://github.com/cartography-cncf/cartography",
        ),
    }

    # Assert - Verify MEMBER relationships to users
    assert check_rels(
        neo4j_session,
        "GitHubTeam",
        "id",
        "GitHubUser",
        "id",
        "MEMBER",
        rel_direction_right=False,
    ) == {
        (
            "https://github.com/orgs/simpsoncorp/teams/team-c",
            "https://github.com/hjsimpson",
        ),
    }

    # Assert - Verify MAINTAINER relationships to users
    assert check_rels(
        neo4j_session,
        "GitHubTeam",
        "id",
        "GitHubUser",
        "id",
        "MAINTAINER",
        rel_direction_right=False,
    ) == {
        (
            "https://github.com/orgs/simpsoncorp/teams/team-c",
            "https://github.com/lmsimpson",
        ),
        (
            "https://github.com/orgs/simpsoncorp/teams/team-c",
            "https://github.com/mbsimpson",
        ),
    }

    # Assert - Verify MEMBER_OF_TEAM relationships between teams
    assert check_rels(
        neo4j_session,
        "GitHubTeam",
        "id",
        "GitHubTeam",
        "id",
        "MEMBER_OF_TEAM",
        rel_direction_right=False,
    ) == {
        (
            "https://github.com/orgs/simpsoncorp/teams/team-d",
            "https://github.com/orgs/simpsoncorp/teams/team-a",
        ),
        (
            "https://github.com/orgs/simpsoncorp/teams/team-d",
            "https://github.com/orgs/simpsoncorp/teams/team-b",
        ),
    }
