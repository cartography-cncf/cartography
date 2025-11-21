from unittest.mock import patch

import cartography.intel.pagerduty.schedules
from tests.data.pagerduty.schedules import LIST_SCHEDULES_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.pagerduty.schedules,
    "get_schedules",
    return_value=LIST_SCHEDULES_DATA,
)
def test_sync_schedules(mock_get_schedules, neo4j_session):
    """
    Test that schedules sync correctly and create proper nodes and relationships
    """
    # Mock PD session (not actually used due to mock)
    mock_pd_session = None

    # Act - Call the sync function
    cartography.intel.pagerduty.schedules.sync_schedules(
        neo4j_session,
        TEST_UPDATE_TAG,
        mock_pd_session,
    )

    # Assert - Use check_nodes() instead of raw Neo4j queries
    # Check schedules
    expected_nodes = {
        ("PI7DH85",),
    }
    assert check_nodes(neo4j_session, "PagerDutySchedule", ["id"]) == expected_nodes

    # Check schedule layers
    expected_layers = {
        ("PI7DH85-Night Shift",),
    }
    assert (
        check_nodes(neo4j_session, "PagerDutyScheduleLayer", ["id"]) == expected_layers
    )

    # Check relationships between schedules and layers
    expected_rels = {
        ("PI7DH85", "PI7DH85-Night Shift"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutySchedule",
            "id",
            "PagerDutyScheduleLayer",
            "id",
            "HAS_LAYER",
            rel_direction_right=True,
        )
        == expected_rels
    )
