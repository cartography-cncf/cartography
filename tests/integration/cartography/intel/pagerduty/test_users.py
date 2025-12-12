from unittest.mock import patch

import cartography.intel.pagerduty.users
from tests.data.pagerduty.users import GET_USERS_DATA
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.pagerduty.users,
    "get_users",
    return_value=GET_USERS_DATA,
)
def test_sync_users(mock_get_users, neo4j_session):
    """
    Test that users sync correctly and create proper nodes
    """
    # Mock PD session (not actually used due to mock)
    mock_pd_session = None

    # Act - Call the sync function
    cartography.intel.pagerduty.users.sync_users(
        neo4j_session,
        TEST_UPDATE_TAG,
        mock_pd_session,
    )

    # Assert - Use check_nodes() instead of raw Neo4j queries
    expected_nodes = {
        ("PXPGF42",),
        ("PAM4FGS",),
    }
    assert check_nodes(neo4j_session, "PagerDutyUser", ["id"]) == expected_nodes
