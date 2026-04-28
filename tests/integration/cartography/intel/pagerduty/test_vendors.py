from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.pagerduty.vendors
import tests.data.pagerduty.vendors
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_vendors(neo4j_session):
    cartography.intel.pagerduty.vendors.load_vendor_data(
        neo4j_session,
        tests.data.pagerduty.vendors.GET_VENDORS_DATA,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.pagerduty.vendors,
    "get_vendors",
    return_value=tests.data.pagerduty.vendors.GET_VENDORS_DATA,
)
def test_load_vendor_data(mock_get, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    # Act
    cartography.intel.pagerduty.vendors.sync_vendors(
        neo4j_session, TEST_UPDATE_TAG, api_session, common_job_parameters
    )

    # Assert nodes exists
    expected_nodes = {("PZQ6AUS", "Amazon CloudWatch")}
    assert (
        check_nodes(neo4j_session, "PagerDutyVendor", ["id", "name"]) == expected_nodes
    )
