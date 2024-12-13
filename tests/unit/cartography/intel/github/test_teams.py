from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.github.teams import _get_team_repos_for_multiple_teams
from cartography.intel.github.teams import _get_team_users_for_multiple_teams
from cartography.intel.github.teams import RepoPermission
from cartography.intel.github.teams import transform_teams
from cartography.intel.github.teams import UserRole
from cartography.intel.github.util import PaginatedGraphqlData

TEST_ORG_DATA = {
    'url': 'https://github.com/testorg',
    'login': 'testorg',
}


@patch('cartography.intel.github.teams._get_team_repos')
def test_get_team_repos_empty_team_list(mock_get_team_repos):
    # Assert that if we pass in empty data then we get back empty data
    assert _get_team_repos_for_multiple_teams(
        [],
        'test-org',
        'https://api.github.com',
        'test-token',
    ) == {}
    mock_get_team_repos.assert_not_called()


@patch('cartography.intel.github.teams._get_team_users')
def test_get_team_users_empty_team_list(mock_get_team_users):
    # Assert that if we pass in empty data then we get back empty data
    assert _get_team_users_for_multiple_teams(
        [],
        'test-org',
        'https://api.github.com',
        'test-token',
    ) == {}
    mock_get_team_users.assert_not_called()


@patch('cartography.intel.github.teams._get_team_repos')
def test_get_team_repos_team_with_no_repos(mock_get_team_repos):
    # Arrange
    team_data = [{'slug': 'team1', 'repositories': {'totalCount': 0}}]

    # Assert that we retrieve data where a team has no repos
    assert _get_team_repos_for_multiple_teams(
        team_data,
        'test-org',
        'https://api.github.com',
        'test-token',
    ) == {'team1': []}
    mock_get_team_repos.assert_not_called()


@patch('cartography.intel.github.teams._get_team_users')
def test_get_team_users_team_with_no_users(mock_get_team_users):
    # Arrange
    team_data = [{'slug': 'team1', 'members': {'totalCount': 0}}]

    # Assert that we retrieve data where a team has no repos
    assert _get_team_users_for_multiple_teams(
        team_data,
        'test-org',
        'https://api.github.com',
        'test-token',
    ) == {'team1': []}
    mock_get_team_users.assert_not_called()


@patch('cartography.intel.github.teams._get_team_repos')
def test_get_team_repos_happy_path(mock_get_team_repos):
    # Arrange
    team_data = [{'slug': 'team1', 'repositories': {'totalCount': 2}}]
    mock_team_repos = MagicMock()
    mock_team_repos.nodes = [{'url': 'https://github.com/org/repo1'}, {'url': 'https://github.com/org/repo2'}]
    mock_team_repos.edges = [{'permission': 'WRITE'}, {'permission': 'READ'}]
    mock_get_team_repos.return_value = mock_team_repos

    # Act + assert that the returned data is correct
    assert _get_team_repos_for_multiple_teams(
        team_data,
        'test-org',
        'https://api.github.com',
        'test-token',
    ) == {
        'team1': [
            RepoPermission('https://github.com/org/repo1', 'WRITE'),
            RepoPermission('https://github.com/org/repo2', 'READ'),
        ],
    }

    # Assert that we did not retry because this was the happy path
    mock_get_team_repos.assert_called_once_with('test-org', 'https://api.github.com', 'test-token', 'team1')


@patch('cartography.intel.github.teams._get_team_users')
def test_get_team_users_happy_path(mock_get_team_users):
    # Arrange
    team_data = [{'slug': 'team1', 'members': {'totalCount': 2}}]
    mock_team_users = MagicMock()
    mock_team_users.nodes = [{'url': 'https://github.com/user1'}, {'url': 'https://github.com/user2'}]
    mock_team_users.edges = [{'role': 'MAINTAINER'}, {'role': 'MEMBER'}]
    mock_get_team_users.return_value = mock_team_users

    # Act + assert that the returned data is correct
    assert _get_team_users_for_multiple_teams(
        team_data,
        'test-org',
        'https://api.github.com',
        'test-token',
    ) == {
        'team1': [
            UserRole('https://github.com/user1', 'MAINTAINER'),
            UserRole('https://github.com/user2', 'MEMBER'),
        ],
    }

    # Assert that we did not retry because this was the happy path
    mock_get_team_users.assert_called_once_with('test-org', 'https://api.github.com', 'test-token', 'team1')


@patch('time.sleep', return_value=None)
@patch('cartography.intel.github.teams._get_team_repos')
@patch('cartography.intel.github.teams.backoff_handler', spec=True)
def test_get_team_repos_github_returns_none(mock_backoff_handler, mock_get_team_repos, mock_sleep):
    # Arrange
    team_data = [{'slug': 'team1', 'repositories': {'totalCount': 1}}]
    mock_team_repos = MagicMock()
    # Set up the condition where GitHub returns a None url and None edge as in #1334.
    mock_team_repos.nodes = [None]
    mock_team_repos.edges = [None]
    mock_get_team_repos.return_value = mock_team_repos

    # Assert we raise an exception
    with pytest.raises(TypeError):
        _get_team_repos_for_multiple_teams(
            team_data,
            'test-org',
            'https://api.github.com',
            'test-token',
        )

    # Assert that we retry and give up
    assert mock_sleep.call_count == 4
    assert mock_get_team_repos.call_count == 5
    assert mock_backoff_handler.call_count == 4


@patch('time.sleep', return_value=None)
@patch('cartography.intel.github.teams._get_team_users')
@patch('cartography.intel.github.teams.backoff_handler', spec=True)
def test_get_team_users_github_returns_none(mock_backoff_handler, mock_get_team_users, mock_sleep):
    # Arrange
    team_data = [{'slug': 'team1', 'members': {'totalCount': 1}}]
    mock_team_users = MagicMock()
    # Set up the condition where GitHub returns a None url and None edge as in #1334.
    mock_team_users.nodes = [None]
    mock_team_users.edges = [None]
    mock_get_team_users.return_value = mock_team_users

    # Assert we raise an exception
    with pytest.raises(TypeError):
        _get_team_users_for_multiple_teams(
            team_data,
            'test-org',
            'https://api.github.com',
            'test-token',
        )

    # Assert that we retry and give up
    assert mock_sleep.call_count == 4
    assert mock_get_team_users.call_count == 5
    assert mock_backoff_handler.call_count == 4


def test_transform_teams_empty_team_data():
    # Arrange
    team_paginated_data = PaginatedGraphqlData(nodes=[], edges=[])
    team_repo_data: dict[str, list[RepoPermission]] = {}
    team_user_data: dict[str, list[UserRole]] = {}

    # Act + assert
    assert transform_teams(team_paginated_data, TEST_ORG_DATA, team_repo_data, team_user_data) == []


def test_transform_teams_team_with_no_repos_no_users():
    # Arrange
    team_paginated_data = PaginatedGraphqlData(
        nodes=[
            {
                'slug': 'team1',
                'url': 'https://github.com/testorg/team1',
                'description': 'Test Team 1',
                'repositories': {'totalCount': 0},
                'members': {'totalCount': 0},
            },
        ],
        edges=[],
    )
    team_repo_data = {'team1': []}
    team_user_data = {'team1': []}

    # Act + Assert
    assert transform_teams(team_paginated_data, TEST_ORG_DATA, team_repo_data, team_user_data) == [
        {
            'name': 'team1',
            'url': 'https://github.com/testorg/team1',
            'description': 'Test Team 1',
            'repo_count': 0,
            'member_count': 0,
            'org_url': 'https://github.com/testorg',
            'org_login': 'testorg',
        },
    ]


def test_transform_teams_team_with_repos():
    # Arrange
    team_paginated_data = PaginatedGraphqlData(
        nodes=[
            {
                'slug': 'team1',
                'url': 'https://github.com/testorg/team1',
                'description': 'Test Team 1',
                'repositories': {'totalCount': 2},
                'members': {'totalCount': 0},
            },
        ],
        edges=[],
    )
    team_repo_data = {
        'team1': [
            RepoPermission('https://github.com/testorg/repo1', 'READ'),
            RepoPermission('https://github.com/testorg/repo2', 'WRITE'),
        ],
    }
    team_user_data = {'team1': []}

    # Act
    assert transform_teams(team_paginated_data, TEST_ORG_DATA, team_repo_data, team_user_data) == [
        {
            'name': 'team1',
            'url': 'https://github.com/testorg/team1',
            'description': 'Test Team 1',
            'repo_count': 2,
            'member_count': 0,
            'org_url': 'https://github.com/testorg',
            'org_login': 'testorg',
            'READ': 'https://github.com/testorg/repo1',
        },
        {
            'name': 'team1',
            'url': 'https://github.com/testorg/team1',
            'description': 'Test Team 1',
            'repo_count': 2,
            'member_count': 0,
            'org_url': 'https://github.com/testorg',
            'org_login': 'testorg',
            'WRITE': 'https://github.com/testorg/repo2',
        },
    ]


def test_transform_teams_team_with_members():
    # Arrange
    team_paginated_data = PaginatedGraphqlData(
        nodes=[
            {
                'slug': 'team1',
                'url': 'https://github.com/testorg/team1',
                'description': 'Test Team 1',
                'repositories': {'totalCount': 0},
                'members': {'totalCount': 2},
            },
        ],
        edges=[],
    )
    team_repo_data = {'team1': []}
    team_user_data = {
        'team1': [
            UserRole('https://github.com/user1', 'MEMBER'),
            UserRole('https://github.com/user2', 'MAINTAINER'),
        ],
    }

    # Act
    assert transform_teams(team_paginated_data, TEST_ORG_DATA, team_repo_data, team_user_data) == [
        {
            'name': 'team1',
            'url': 'https://github.com/testorg/team1',
            'description': 'Test Team 1',
            'repo_count': 0,
            'member_count': 2,
            'org_url': 'https://github.com/testorg',
            'org_login': 'testorg',
            'MEMBER': 'https://github.com/user1',
        },
        {
            'name': 'team1',
            'url': 'https://github.com/testorg/team1',
            'description': 'Test Team 1',
            'repo_count': 0,
            'member_count': 2,
            'org_url': 'https://github.com/testorg',
            'org_login': 'testorg',
            'MAINTAINER': 'https://github.com/user2',
        },
    ]


def test_transform_teams_team_with_repos_and_members():
    # Arrange
    team_paginated_data = PaginatedGraphqlData(
        nodes=[
            {
                'slug': 'team1',
                'url': 'https://github.com/testorg/team1',
                'description': 'Test Team 1',
                'repositories': {'totalCount': 2},
                'members': {'totalCount': 2},
            },
        ],
        edges=[],
    )
    team_repo_data = {
        'team1': [
            RepoPermission('https://github.com/testorg/repo1', 'READ'),
            RepoPermission('https://github.com/testorg/repo2', 'WRITE'),
        ],
    }
    team_user_data = {
        'team1': [
            UserRole('https://github.com/user1', 'MEMBER'),
            UserRole('https://github.com/user2', 'MAINTAINER'),
        ],
    }

    # Act
    assert transform_teams(team_paginated_data, TEST_ORG_DATA, team_repo_data, team_user_data) == [
        {
            'name': 'team1',
            'url': 'https://github.com/testorg/team1',
            'description': 'Test Team 1',
            'repo_count': 2,
            'member_count': 2,
            'org_url': 'https://github.com/testorg',
            'org_login': 'testorg',
            'READ': 'https://github.com/testorg/repo1',
        },
        {
            'name': 'team1',
            'url': 'https://github.com/testorg/team1',
            'description': 'Test Team 1',
            'repo_count': 2,
            'member_count': 2,
            'org_url': 'https://github.com/testorg',
            'org_login': 'testorg',
            'WRITE': 'https://github.com/testorg/repo2',
        },
        {
            'name': 'team1',
            'url': 'https://github.com/testorg/team1',
            'description': 'Test Team 1',
            'repo_count': 2,
            'member_count': 2,
            'org_url': 'https://github.com/testorg',
            'org_login': 'testorg',
            'MEMBER': 'https://github.com/user1',
        },
        {
            'name': 'team1',
            'url': 'https://github.com/testorg/team1',
            'description': 'Test Team 1',
            'repo_count': 2,
            'member_count': 2,
            'org_url': 'https://github.com/testorg',
            'org_login': 'testorg',
            'MAINTAINER': 'https://github.com/user2',
        },
    ]


def test_transform_teams_multiple_teams():
    # Arrange
    team_paginated_data = PaginatedGraphqlData(
        nodes=[
            {
                'slug': 'team1',
                'url': 'https://github.com/testorg/team1',
                'description': 'Test Team 1',
                'repositories': {'totalCount': 1},
                'members': {'totalCount': 0},
            },
            {
                'slug': 'team2',
                'url': 'https://github.com/testorg/team2',
                'description': 'Test Team 2',
                'repositories': {'totalCount': 0},
                'members': {'totalCount': 1},
            },
        ],
        edges=[],
    )
    team_repo_data = {
        'team1': [
            RepoPermission('https://github.com/testorg/repo1', 'ADMIN'),
        ],
        'team2': [],
    }
    team_user_data = {
        'team1': [],
        'team2': [
            UserRole('https://github.com/user1', 'MEMBER'),
        ],
    }

    # Act + assert
    assert transform_teams(team_paginated_data, TEST_ORG_DATA, team_repo_data, team_user_data) == [
        {
            'name': 'team1',
            'url': 'https://github.com/testorg/team1',
            'description': 'Test Team 1',
            'repo_count': 1,
            'member_count': 0,
            'org_url': 'https://github.com/testorg',
            'org_login': 'testorg',
            'ADMIN': 'https://github.com/testorg/repo1',
        },
        {
            'name': 'team2',
            'url': 'https://github.com/testorg/team2',
            'description': 'Test Team 2',
            'repo_count': 0,
            'member_count': 1,
            'org_url': 'https://github.com/testorg',
            'org_login': 'testorg',
            'MEMBER': 'https://github.com/user1',
        },
    ]
