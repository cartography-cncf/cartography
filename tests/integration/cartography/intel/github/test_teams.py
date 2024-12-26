from unittest.mock import patch

import cartography.intel.github.teams
from cartography.intel.github.teams import sync_github_teams
from tests.data.github.teams import GH_TEAM_CHILD_TEAM
from tests.data.github.teams import GH_TEAM_DATA
from tests.data.github.teams import GH_TEAM_REPOS
from tests.data.github.teams import GH_TEAM_USERS
from tests.integration.cartography.intel.github import test_repos
from tests.integration.cartography.intel.github import test_users
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {'UPDATE_TAG': TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://fake.github.net/graphql/"
FAKE_API_KEY = 'asdf'


@patch.object(cartography.intel.github.teams, '_get_child_teams', return_value=GH_TEAM_CHILD_TEAM)
@patch.object(cartography.intel.github.teams, '_get_team_users', return_value=GH_TEAM_USERS)
@patch.object(cartography.intel.github.teams, '_get_team_repos', return_value=GH_TEAM_REPOS)
@patch.object(cartography.intel.github.teams, 'get_teams', return_value=GH_TEAM_DATA)
def test_sync_github_teams(mock_teams, mock_team_repos, mock_team_users, mock_child_teams, neo4j_session):
    # Arrange
    test_repos._ensure_local_neo4j_has_test_data(neo4j_session)
    test_users._ensure_local_neo4j_has_test_data(neo4j_session)
    # Arrange: Add another org to make sure we don't attach a node to the wrong org
    neo4j_session.run('''
        MERGE (g:GitHubOrganization{id: "this should have no attachments"})
    ''')

    # Act
    sync_github_teams(neo4j_session, TEST_JOB_PARAMS, FAKE_API_KEY, TEST_GITHUB_URL, 'example_org')

    # Assert
    assert check_nodes(neo4j_session, 'GitHubTeam', ['id', 'url', 'name']) == {
        (
            'https://github.com/orgs/example_org/teams/team-a',
            'https://github.com/orgs/example_org/teams/team-a',
            'team-a',
        ),
        (
            'https://github.com/orgs/example_org/teams/team-b',
            'https://github.com/orgs/example_org/teams/team-b',
            'team-b',
        ),
        (
            'https://github.com/orgs/example_org/teams/team-c',
            'https://github.com/orgs/example_org/teams/team-c',
            'team-c',
        ),
        (
            'https://github.com/orgs/example_org/teams/team-d',
            'https://github.com/orgs/example_org/teams/team-d',
            'team-d',
        ),
        (
            'https://github.com/orgs/example_org/teams/team-e',
            'https://github.com/orgs/example_org/teams/team-e',
            'team-e',
        ),
    }
    assert check_rels(
        neo4j_session,
        'GitHubTeam', 'id',
        'GitHubOrganization', 'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        (
            'https://github.com/orgs/example_org/teams/team-a',
            'https://github.com/example_org',
        ),
        (
            'https://github.com/orgs/example_org/teams/team-b',
            'https://github.com/example_org',
        ),
        (
            'https://github.com/orgs/example_org/teams/team-c',
            'https://github.com/example_org',
        ),
        (
            'https://github.com/orgs/example_org/teams/team-d',
            'https://github.com/example_org',
        ),
        (
            'https://github.com/orgs/example_org/teams/team-e',
            'https://github.com/example_org',
        ),
    }
    assert check_rels(
        neo4j_session,
        'GitHubTeam', 'id',
        'GitHubRepository', 'id',
        'ADMIN',
        rel_direction_right=True,
    ) == {
        (
            'https://github.com/orgs/example_org/teams/team-b',
            'https://github.com/example_org/sample_repo',
        ),
    }
    assert check_rels(
        neo4j_session,
        'GitHubTeam', 'id',
        'GitHubRepository', 'id',
        'WRITE',
        rel_direction_right=True,
    ) == {
        (
            'https://github.com/orgs/example_org/teams/team-b',
            'https://github.com/example_org/SampleRepo2',
        ),
    }
    assert check_rels(
        neo4j_session,
        'GitHubTeam', 'id',
        'GitHubRepository', 'id',
        'READ',
        rel_direction_right=True,
    ) == {
        ('https://github.com/orgs/example_org/teams/team-b', 'https://github.com/lyft/cartography'),
    }
    assert check_rels(
        neo4j_session,
        'GitHubTeam', 'id',
        'GitHubUser', 'id',
        'MEMBER',
        rel_direction_right=False,
    ) == {
        ('https://github.com/orgs/example_org/teams/team-c', 'https://example.com/hjsimpson'),
    }
    assert check_rels(
        neo4j_session,
        'GitHubTeam', 'id',
        'GitHubUser', 'id',
        'MAINTAINER',
        rel_direction_right=False,
    ) == {
        ('https://github.com/orgs/example_org/teams/team-c', 'https://example.com/lmsimpson'),
        ('https://github.com/orgs/example_org/teams/team-c', 'https://example.com/mbsimpson'),
    }
    assert check_rels(
        neo4j_session,
        'GitHubTeam', 'id',
        'GitHubTeam', 'id',
        'MEMBER_OF_TEAM',
        rel_direction_right=False,
    ) == {
        ('https://github.com/orgs/example_org/teams/team-d', 'https://github.com/orgs/example_org/teams/team-a'),
        ('https://github.com/orgs/example_org/teams/team-d', 'https://github.com/orgs/example_org/teams/team-b'),
    }
