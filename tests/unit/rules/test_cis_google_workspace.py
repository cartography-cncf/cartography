from cartography.rules.data.rules.cis_google_workspace import (
    cis_gw_4_1_1_1_admin_2sv_not_enforced,
)
from cartography.rules.data.rules.cis_google_workspace import (
    cis_gw_4_1_1_3_user_2sv_not_enforced,
)
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module


def test_rules_registered_and_metadata():
    """Verify all rules have correct metadata."""
    rules = [
        cis_gw_4_1_1_3_user_2sv_not_enforced,
        cis_gw_4_1_1_1_admin_2sv_not_enforced,
    ]

    for rule in rules:
        assert rule.version == "1.0.0"
        assert rule.modules == {Module.GOOGLEWORKSPACE}
        # Check that the rule has CIS framework reference
        assert rule.has_framework("cis", "googleworkspace", "1.4")
        assert rule.references
        assert len(rule.references) >= 1


def test_rule_names_follow_cis_convention():
    """Verify rule names follow CIS naming convention."""
    rules = [
        cis_gw_4_1_1_3_user_2sv_not_enforced,
        cis_gw_4_1_1_1_admin_2sv_not_enforced,
    ]

    for rule in rules:
        assert rule.name.startswith(
            "CIS Google Workspace"
        ), f"Rule {rule.id} name should start with 'CIS Google Workspace'"


def test_facts_have_expected_structure():
    """Verify facts have required fields and valid queries."""
    expected_fact_ids = {
        "gw_user_2sv_not_enforced",
        "gw_admin_2sv_not_enforced",
    }

    for rule in (
        cis_gw_4_1_1_3_user_2sv_not_enforced,
        cis_gw_4_1_1_1_admin_2sv_not_enforced,
    ):
        assert len(rule.facts) == 1
        fact = rule.facts[0]
        assert fact.id in expected_fact_ids
        assert fact.module == Module.GOOGLEWORKSPACE
        assert fact.maturity == Maturity.EXPERIMENTAL
        assert "MATCH" in fact.cypher_query
        assert "RETURN" in fact.cypher_query
        assert fact.cypher_visual_query.strip().split()[0] in {"MATCH", "WITH"}
        assert "COUNT" in fact.cypher_count_query


def test_output_models_are_distinct():
    """Verify each rule has its own output model (not shared)."""
    rules = [
        cis_gw_4_1_1_3_user_2sv_not_enforced,
        cis_gw_4_1_1_1_admin_2sv_not_enforced,
    ]

    output_models = [rule.output_model for rule in rules]
    # All output models should be unique classes
    assert len(set(output_models)) == len(output_models)
