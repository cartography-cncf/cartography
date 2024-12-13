from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.github.repos import _get_repo_collaborators_for_multiple_repos


@patch('time.sleep', return_value=None)
@patch('cartography.intel.github.repos._get_repo_collaborators')
@patch('cartography.intel.github.repos.backoff_handler', spec=True)
def test_get_team_users_github_returns_none(mock_backoff_handler, mock_get_team_collaborators, mock_sleep):
    """
    This test happens to use 'OUTSIDE' affiliation, but it's irrelevant for the test, it just needs either valid value.
    """
    # Arrange
    repo_data = [{'name': 'repo1', 'url': 'https://github.com/repo1', 'outsideCollaborators': {'totalCount': 1}}]
    mock_repo_collabs = MagicMock()
    # Set up the condition where GitHub returns a None url and None edge as in #1334.
    mock_repo_collabs.nodes = [None]
    mock_repo_collabs.edges = [None]
    mock_get_team_collaborators.return_value = mock_repo_collabs

    # Assert we raise an exception
    with pytest.raises(TypeError):
        _get_repo_collaborators_for_multiple_repos(
            repo_data,
            'OUTSIDE',
            'test-org',
            'https://api.github.com',
            'test-token',
        )

    # Assert that we retry and give up
    assert mock_sleep.call_count == 4
    assert mock_get_team_collaborators.call_count == 5
    assert mock_backoff_handler.call_count == 4
