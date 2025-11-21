from unittest.mock import patch

import cartography.intel.pagerduty.vendors
from tests.data.pagerduty.vendors import GET_VENDORS_DATA
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.pagerduty.vendors,
    "get_vendors",
    return_value=GET_VENDORS_DATA,
)
def test_sync_vendors(mock_get_vendors, neo4j_session):
    """
    Test that vendors sync correctly and create proper nodes
    """
    # Mock PD session (not actually used due to mock)
    mock_pd_session = None

    # Act - Call the sync function
    cartography.intel.pagerduty.vendors.sync_vendors(
        neo4j_session,
        TEST_UPDATE_TAG,
        mock_pd_session,
    )

    # Assert - Use check_nodes() instead of raw Neo4j queries
    expected_nodes = {
        ("PZQ6AUS",),
    }
    assert check_nodes(neo4j_session, "PagerDutyVendor", ["id"]) == expected_nodes
