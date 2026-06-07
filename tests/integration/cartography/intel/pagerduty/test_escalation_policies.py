from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.pagerduty.escalation_policies
import tests.data.pagerduty.escalation_policies
from tests.integration.cartography.intel.pagerduty.test_schedules import (
    _ensure_local_neo4j_has_test_schedules,
)
from tests.integration.cartography.intel.pagerduty.test_services import (
    _ensure_local_neo4j_has_test_services,
)
from tests.integration.cartography.intel.pagerduty.test_teams import (
    _ensure_local_neo4j_has_test_teams,
)
from tests.integration.cartography.intel.pagerduty.test_users import (
    _ensure_local_neo4j_has_test_users,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.pagerduty.escalation_policies,
    "get_escalation_policies",
    return_value=tests.data.pagerduty.escalation_policies.GET_ESCALATION_POLICY_DATA,
)
def test_load_escalation_policy_data(mock_get, neo4j_session):
    # Arrange
    api_session = Mock()
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}
    _ensure_local_neo4j_has_test_users(neo4j_session)
    _ensure_local_neo4j_has_test_teams(neo4j_session)
    _ensure_local_neo4j_has_test_services(neo4j_session)
    _ensure_local_neo4j_has_test_schedules(neo4j_session)

    # Act
    cartography.intel.pagerduty.escalation_policies.sync_escalation_policies(
        neo4j_session, TEST_UPDATE_TAG, api_session, common_job_parameters
    )

    # Assert nodes exists
    expected_nodes = {
        ("PANZZEQ", "Engineering Escalation Policy"),
    }
    assert (
        check_nodes(neo4j_session, "PagerDutyEscalationPolicy", ["id", "name"])
        == expected_nodes
    )
    expected_nodes = {("PANZZEA", 30)}
    assert (
        check_nodes(
            neo4j_session,
            "PagerDutyEscalationPolicyRule",
            ["id", "escalation_delay_in_minutes"],
        )
        == expected_nodes
    )

    # Assert Policy are linked to the correct Service
    expected_rels = {
        ("PANZZEQ", "PIJ90N7"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutyEscalationPolicy",
            "id",
            "PagerDutyService",
            "id",
            "ASSOCIATED_WITH",
            rel_direction_right=False,
        )
        == expected_rels
    )
    # Assert Policy are linked to the correct Team
    expected_rels = {
        ("PANZZEQ", "PQ9K7I8"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutyEscalationPolicy",
            "id",
            "PagerDutyTeam",
            "id",
            "ASSOCIATED_WITH",
            rel_direction_right=False,
        )
        == expected_rels
    )
    # Assert Policy is linked to Rule
    expected_rels = {
        ("PANZZEA", "PANZZEQ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutyEscalationPolicyRule",
            "id",
            "PagerDutyEscalationPolicy",
            "id",
            "HAS_RULE",
            rel_direction_right=False,
        )
        == expected_rels
    )
    # Assert Rule is linked to User
    expected_rels = {
        ("PANZZEA", "PXPGF42"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutyEscalationPolicyRule",
            "id",
            "PagerDutyUser",
            "id",
            "ASSOCIATED_WITH",
            rel_direction_right=False,
        )
        == expected_rels
    )
    # Assert Rule is linked to Schedule
    expected_rels = {
        ("PANZZEA", "PI7DH85"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutyEscalationPolicyRule",
            "id",
            "PagerDutySchedule",
            "id",
            "ASSOCIATED_WITH",
            rel_direction_right=True,
        )
        == expected_rels
    )
