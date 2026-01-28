from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.pagerduty.schedules
import tests.data.pagerduty.schedules
from tests.integration.cartography.intel.pagerduty.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_schedules(neo4j_session):
    schedules, _ = cartography.intel.pagerduty.schedules.transform_schedules(
        tests.data.pagerduty.schedules.LIST_SCHEDULES_DATA,
    )
    cartography.intel.pagerduty.schedules.load_schedule_data(
        neo4j_session,
        schedules,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.pagerduty.schedules,
    "get_schedules",
    return_value=tests.data.pagerduty.schedules.LIST_SCHEDULES_DATA,
)
def test_load_schedule_data(mock_get, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}
    _ensure_local_neo4j_has_test_users(neo4j_session)

    # Act
    cartography.intel.pagerduty.schedules.sync_schedules(
        neo4j_session, TEST_UPDATE_TAG, api_session, common_job_parameters
    )

    # Assert nodes exists
    expected_nodes = {
        ("PI7DH85", "Daily Engineering Rotation"),
    }
    assert (
        check_nodes(neo4j_session, "PagerDutySchedule", ["id", "name"])
        == expected_nodes
    )
    expected_nodes = {("PI7DH85-Night Shift", "Night Shift")}
    assert (
        check_nodes(neo4j_session, "PagerDutyScheduleLayer", ["id", "name"])
        == expected_nodes
    )
    # Assert Schedule is linked to User
    expected_rels = {
        ("PXPGF42", "PI7DH85"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutyUser",
            "id",
            "PagerDutySchedule",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )
    # Assert Layer is linked to Schedule
    expected_rels = {
        ("PI7DH85-Night Shift", "PI7DH85"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutyScheduleLayer",
            "id",
            "PagerDutySchedule",
            "id",
            "HAS_LAYER",
            rel_direction_right=False,
        )
        == expected_rels
    )
    # Assert Layer is linked to User
    expected_rels = {
        ("PXPGF42", "PI7DH85-Night Shift"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutyUser",
            "id",
            "PagerDutyScheduleLayer",
            "id",
            "MEMBER_OF",
            rel_direction_right=True,
        )
        == expected_rels
    )
