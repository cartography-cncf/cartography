from cartography.rules.data.rules.cis_google_workspace import (
    googleworkspace_admins_without_enforced_2sv,
)
from cartography.rules.data.rules.cis_google_workspace import (
    googleworkspace_super_admin_accounts_used_for_daily_admin,
)
from cartography.rules.data.rules.cis_google_workspace import (
    googleworkspace_too_few_super_admin_accounts,
)
from cartography.rules.data.rules.cis_google_workspace import (
    googleworkspace_too_many_super_admin_accounts,
)
from cartography.rules.data.rules.cis_google_workspace import (
    googleworkspace_users_without_enforced_2sv,
)
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module


def test_rules_registered_and_metadata():
    """Verify all rules have correct metadata."""
    rules = [
        googleworkspace_too_few_super_admin_accounts,
        googleworkspace_too_many_super_admin_accounts,
        googleworkspace_super_admin_accounts_used_for_daily_admin,
        googleworkspace_users_without_enforced_2sv,
        googleworkspace_admins_without_enforced_2sv,
    ]

    for rule in rules:
        assert rule.version == "1.0.0"
        assert rule.modules == {Module.GOOGLEWORKSPACE}
        # Check that the rule has CIS framework reference
        assert rule.has_framework("cis", "googleworkspace", "1.3")
        assert rule.references
        assert len(rule.references) >= 1


def test_rule_names_are_security_names():
    """Verify rule names do not include compliance prefixes."""
    rules = [
        googleworkspace_too_few_super_admin_accounts,
        googleworkspace_too_many_super_admin_accounts,
        googleworkspace_super_admin_accounts_used_for_daily_admin,
        googleworkspace_users_without_enforced_2sv,
        googleworkspace_admins_without_enforced_2sv,
    ]

    for rule in rules:
        assert not rule.name.startswith("CIS Google Workspace")
        assert ":" not in rule.name


def test_facts_have_expected_structure():
    """Verify facts have required fields and valid queries."""
    expected_fact_ids = {
        "gw_super_admin_count_too_low",
        "gw_super_admin_count_too_high",
        "gw_super_admin_with_delegated_admin_role",
        "gw_user_2sv_not_enforced",
        "gw_admin_2sv_not_enforced",
    }

    for rule in (
        googleworkspace_too_few_super_admin_accounts,
        googleworkspace_too_many_super_admin_accounts,
        googleworkspace_super_admin_accounts_used_for_daily_admin,
        googleworkspace_users_without_enforced_2sv,
        googleworkspace_admins_without_enforced_2sv,
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
        googleworkspace_too_few_super_admin_accounts,
        googleworkspace_too_many_super_admin_accounts,
        googleworkspace_super_admin_accounts_used_for_daily_admin,
        googleworkspace_users_without_enforced_2sv,
        googleworkspace_admins_without_enforced_2sv,
    ]

    output_models = [rule.output_model for rule in rules]
    # All output models should be unique classes
    assert len(set(output_models)) == len(output_models)


def test_admin_2sv_rule_includes_delegated_admins():
    fact = googleworkspace_admins_without_enforced_2sv.facts[0]

    assert "u.is_delegated_admin" in fact.cypher_query
    assert "u.is_delegated_admin" in fact.cypher_visual_query
    assert "u.is_delegated_admin" in fact.cypher_count_query


def test_super_admin_rules_use_is_admin_as_super_admin_signal():
    low_fact = googleworkspace_too_few_super_admin_accounts.facts[0]
    high_fact = googleworkspace_too_many_super_admin_accounts.facts[0]
    dual_role_fact = googleworkspace_super_admin_accounts_used_for_daily_admin.facts[0]

    assert "coalesce(u.is_admin, false) = true" in low_fact.cypher_query
    assert "super_admin_count <= 1" in low_fact.cypher_query

    assert "coalesce(u.is_admin, false) = true" in high_fact.cypher_query
    assert "super_admin_count > 4" in high_fact.cypher_query

    assert "coalesce(u.is_admin, false) = true" in dual_role_fact.cypher_query
    assert "coalesce(u.is_delegated_admin, false) = true" in dual_role_fact.cypher_query
    assert "coalesce(u.is_admin, false) = true" in dual_role_fact.cypher_count_query
    assert (
        "coalesce(u.is_delegated_admin, false) = true"
        not in dual_role_fact.cypher_count_query
    )
