from cartography.rules.data.rules.google_workspace_cis import (
    google_workspace_cis_1_1_enforce_2sv,
)
from cartography.rules.data.rules.google_workspace_cis import (
    google_workspace_cis_1_2_admins_enforced_2sv,
)
from cartography.rules.data.rules.google_workspace_cis import (
    google_workspace_cis_2_1_high_risk_oauth,
)
from cartography.rules.spec.model import Module


def test_rules_registered_and_metadata():
    rules = [
        google_workspace_cis_1_1_enforce_2sv,
        google_workspace_cis_1_2_admins_enforced_2sv,
        google_workspace_cis_2_1_high_risk_oauth,
    ]

    for rule in rules:
        assert rule.version == "0.1.0"
        assert rule.output_model.__name__ == "GoogleWorkspaceCISFinding"
        assert rule.modules == {Module.GOOGLEWORKSPACE}
        assert rule.tags[0].startswith("cis:")
        assert rule.references


def test_facts_have_expected_structure():
    expected_fact_ids = {
        "gw-cis-1-1-2sv-not-enforced",
        "gw-cis-1-2-admin-2sv-not-enforced",
        "gw-cis-2-1-high-risk-oauth-scopes",
    }

    for rule in (
        google_workspace_cis_1_1_enforce_2sv,
        google_workspace_cis_1_2_admins_enforced_2sv,
        google_workspace_cis_2_1_high_risk_oauth,
    ):
        assert len(rule.facts) == 1
        fact = rule.facts[0]
        assert fact.id in expected_fact_ids
        assert fact.module == Module.GOOGLEWORKSPACE
        assert "MATCH" in fact.cypher_query
        assert "RETURN" in fact.cypher_query
        assert fact.cypher_visual_query.strip().split()[0] in {"MATCH", "WITH"}
