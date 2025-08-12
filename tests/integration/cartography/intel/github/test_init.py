import base64
import json
from unittest.mock import patch

from pytest import raises
from requests import exceptions

import cartography.config
import cartography.intel.github

TEST_UPDATE_TAG = 123456789


def _make_config() -> cartography.config.Config:
    auth_config = {
        "organization": [
            {
                "token": "fake",
                "url": "https://github.com",
                "name": "simpsoncorp",
            },
        ]
    }
    encoded = base64.b64encode(json.dumps(auth_config).encode()).decode()
    return cartography.config.Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        github_config=encoded,
    )


@patch.object(cartography.intel.github.teams, "sync_github_teams", return_value=None)
@patch.object(cartography.intel.github.repos, "sync", return_value=None)
@patch.object(
    cartography.intel.github.users,
    "sync",
    side_effect=exceptions.RequestException("unauthorized"),
)
def test_start_github_ingestion_raises(
    mock_users_sync,
    mock_repos_sync,
    mock_teams_sync,
    neo4j_session,
):
    config = _make_config()
    with raises(exceptions.RequestException):
        cartography.intel.github.start_github_ingestion(neo4j_session, config)
    assert mock_users_sync.call_count == 1
    assert mock_repos_sync.call_count == 0
    assert mock_teams_sync.call_count == 0
