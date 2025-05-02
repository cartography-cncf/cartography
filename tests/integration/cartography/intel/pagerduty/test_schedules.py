import cartography.intel.pagerduty.schedules
import tests.data.pagerduty.schedules

TEST_UPDATE_TAG = 123456789


def test_load_schedule_data(neo4j_session):
    schedule_data = tests.data.pagerduty.schedules.LIST_SCHEDULES_DATA
    cartography.intel.pagerduty.schedules.load_schedule_data(
        neo4j_session,
        schedule_data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "PI7DH85",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:PagerDutySchedule) RETURN n.id;
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == expected_nodes

    expected_layers = {
        "PI7DH85-Night Shift",
    }
    layers = neo4j_session.run(
        """
        MATCH (:PagerDutySchedule{id:"PI7DH85"})-[:HAS_LAYER]->(n:PagerDutyScheduleLayer)
        RETURN n.id;
        """,
    )
    actual_layers = {n["n.id"] for n in layers}
    assert actual_layers == expected_layers
