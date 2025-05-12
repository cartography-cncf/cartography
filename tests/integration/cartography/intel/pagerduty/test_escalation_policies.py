import cartography.intel.pagerduty.escalation_policies
import tests.data.pagerduty.escalation_policies

TEST_UPDATE_TAG = 123456789


def test_load_escalation_policy_data(neo4j_session):
    escalation_policy_data = (
        tests.data.pagerduty.escalation_policies.GET_ESCALATION_POLICY_DATA
    )
    cartography.intel.pagerduty.escalation_policies.load_escalation_policy_data(
        neo4j_session,
        escalation_policy_data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "PANZZEQ",
    }
    nodes = neo4j_session.run(
        """
        MATCH (n:PagerDutyEscalationPolicy) RETURN n.id;
        """,
    )
    actual_nodes = {n["n.id"] for n in nodes}
    assert actual_nodes == expected_nodes

    expected_rules = {
        "PANZZEQ",
    }
    rules = neo4j_session.run(
        """
        MATCH (:PagerDutyEscalationPolicy{id:"PANZZEQ"})-[:HAS_RULE]->(n:PagerDutyEscalationPolicyRule)
        RETURN n.id;
        """,
    )
    actual_rules = {n["n.id"] for n in rules}
    assert actual_rules == expected_rules
