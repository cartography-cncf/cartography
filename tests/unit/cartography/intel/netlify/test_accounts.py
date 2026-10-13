from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

import cartography.intel.netlify.accounts
import tests.data.netlify.accounts

TEST_BASE_URL = "https://api.netlify.com/api/v1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.netlify.accounts,
    "get_netlify_accounts",
    return_value=tests.data.netlify.accounts.NETLIFY_ACCOUNTS,
)
def test_sync_netlify_account_rejects_unknown_slug(mock_get) -> None:
    """
    An unrecognised slug has to fail loudly. Syncing nothing would let every downstream cleanup
    job delete the previous run's data.
    """
    # Arrange
    neo4j_session = MagicMock()
    api_session = MagicMock(spec=requests.Session)

    # Act / Assert
    with pytest.raises(ValueError, match="was not found"):
        cartography.intel.netlify.accounts.sync_netlify_account(
            neo4j_session,
            api_session,
            TEST_BASE_URL,
            "not-a-real-team",
            TEST_UPDATE_TAG,
        )

    # Assert the failure happened before anything was written
    assert neo4j_session.method_calls == []
