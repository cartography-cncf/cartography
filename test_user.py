import pytest
from unittest.mock import patch, Mock
import requests

import cartography.intel.github.users as users


def test_sync_fails_on_auth_error():
    """Test that sync raises exception on authentication error"""
    with patch.object(users, 'get_users', side_effect=requests.exceptions.HTTPError("401 Unauthorized")), \
         patch.object(users, 'get_enterprise_owners', side_effect=requests.exceptions.HTTPError("401 Unauthorized")):
        neo4j_session = Mock()
        mock_summary = Mock()
        mock_summary.counters.contains_updates = False
        neo4j_session.write_transaction = Mock(return_value=mock_summary)

        with pytest.raises(requests.exceptions.HTTPError):
            users.sync(
                neo4j_session=neo4j_session,
                common_job_parameters={"UPDATE_TAG": 123},
                github_api_key="invalid_token",
                github_url="https://api.github.com/graphql",
                organization="test_org"
            )


def test_sync_fails_on_no_data():
    """Test that sync raises exception when no data retrieved"""
    with patch.object(users, 'get_users') as mock_get_users, \
         patch.object(users, 'get_enterprise_owners') as mock_get_owners:
        mock_get_users.return_value = ([], {"url": "org-url", "login": "org"})
        mock_get_owners.return_value = ([], {"url": "org-url", "login": "org"})

        neo4j_session = Mock()
        mock_summary = Mock()
        mock_summary.counters.contains_updates = False
        neo4j_session.write_transaction = Mock(return_value=mock_summary)

        with pytest.raises(RuntimeError, match="GitHub sync failed to retrieve any user or enterprise owner data"):
            users.sync(
                neo4j_session=neo4j_session,
                common_job_parameters={"UPDATE_TAG": 123},
                github_api_key="valid_token",
                github_url="https://api.github.com/graphql",
                organization="test_org"
            )


def test_sync_succeeds_on_partial_data():
    """Test that sync does not raise exception when partial data is present"""
    with patch.object(users, 'get_users') as mock_get_users, \
         patch.object(users, 'get_enterprise_owners') as mock_get_owners:
        # Partial data: users present, owners empty
        mock_get_users.return_value = ([{"node": {"url": "user-url"}, "hasTwoFactorEnabled": True, "role": "ADMIN"}], {"url": "org-url", "login": "org"})
        mock_get_owners.return_value = ([], {"url": "org-url", "login": "org"})

        neo4j_session = Mock()
        mock_summary = Mock()
        mock_summary.counters.contains_updates = False
        neo4j_session.write_transaction = Mock(return_value=mock_summary)

        # Should not raise
        users.sync(
            neo4j_session=neo4j_session,
            common_job_parameters={"UPDATE_TAG": 123},
            github_api_key="valid_token",
            github_url="https://api.github.com/graphql",
            organization="test_org"
        )
