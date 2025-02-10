import cartography.intel.pagerduty.vendors
import tests.data.pagerduty.vendors

TEST_UPDATE_TAG = 123456789


def test_load_user_data(neo4j_session):
    vendor_data = tests.data.pagerduty.vendors.GET_VENDORS_DATA
    cartography.intel.pagerduty.vendors.load_vendor_data(
        neo4j_session,
        vendor_data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "PZQ6AUS",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:PagerDutyVendor) RETURN n.id;
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == expected_nodes
