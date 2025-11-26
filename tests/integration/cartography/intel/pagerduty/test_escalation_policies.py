from unittest.mock import patch

import cartography.intel.pagerduty.escalation_policies
from tests.data.pagerduty.escalation_policies import GET_ESCALATION_POLICY_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.pagerduty.escalation_policies,
    "get_escalation_policies",
    return_value=GET_ESCALATION_POLICY_DATA,
)
def test_sync_escalation_policies(mock_get_escalation_policies, neo4j_session):
    """
    Test that escalation policies sync correctly and create proper nodes and relationships
    """
    # Mock PD session (not actually used due to mock)
    mock_pd_session = None

    # Act - Call the sync function
    cartography.intel.pagerduty.escalation_policies.sync_escalation_policies(
        neo4j_session,
        TEST_UPDATE_TAG,
        mock_pd_session,
    )

    # Assert - Use check_nodes() instead of raw Neo4j queries
    # Check escalation policies
    expected_nodes = {
        ("PANZZEQ",),
    }
    assert (
        check_nodes(neo4j_session, "PagerDutyEscalationPolicy", ["id"])
        == expected_nodes
    )

    # Check escalation policy rules
    expected_rules = {
        ("PANZZEQ",),
    }
    assert (
        check_nodes(neo4j_session, "PagerDutyEscalationPolicyRule", ["id"])
        == expected_rules
    )

    # Check relationships between policies and rules
    expected_rels = {
        ("PANZZEQ", "PANZZEQ"),
    }
    assert (
        check_rels(
            neo4j_session,
            "PagerDutyEscalationPolicy",
            "id",
            "PagerDutyEscalationPolicyRule",
            "id",
            "HAS_RULE",
            rel_direction_right=True,
        )
        == expected_rels
    )
