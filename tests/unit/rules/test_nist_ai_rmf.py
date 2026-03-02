from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.nist_ai_rmf import nist_ai_admin_ai_app_authorizations
from cartography.rules.data.rules.nist_ai_rmf import nist_ai_provider_api_key_hygiene
from cartography.rules.data.rules.nist_ai_rmf import nist_ai_third_party_app_inventory
from cartography.rules.data.rules.nist_ai_rmf import (
    nist_ai_third_party_app_sensitive_scopes,
)
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module


def test_nist_ai_rules_registered_and_metadata():
    expected_rules = {
        "nist_ai_third_party_app_inventory": nist_ai_third_party_app_inventory,
        "nist_ai_third_party_app_sensitive_scopes": nist_ai_third_party_app_sensitive_scopes,
        "nist_ai_admin_ai_app_authorizations": nist_ai_admin_ai_app_authorizations,
        "nist_ai_provider_api_key_hygiene": nist_ai_provider_api_key_hygiene,
    }

    for rule_id, rule_obj in expected_rules.items():
        assert rule_id in RULES
        assert RULES[rule_id] is rule_obj
        assert rule_obj.version == "0.1.0"
        assert rule_obj.references
        assert rule_obj.has_framework("nist-ai-rmf", revision="1.0")


def test_nist_ai_rule_modules():
    assert nist_ai_third_party_app_inventory.modules == {Module.CROSS_CLOUD}
    assert nist_ai_third_party_app_sensitive_scopes.modules == {Module.CROSS_CLOUD}
    assert nist_ai_admin_ai_app_authorizations.modules == {Module.GOOGLEWORKSPACE}
    assert nist_ai_provider_api_key_hygiene.modules == {Module.OPENAI, Module.ANTHROPIC}


def test_nist_ai_fact_structure_and_maturity():
    rules = (
        nist_ai_third_party_app_inventory,
        nist_ai_third_party_app_sensitive_scopes,
        nist_ai_admin_ai_app_authorizations,
        nist_ai_provider_api_key_hygiene,
    )

    for rule in rules:
        for fact in rule.facts:
            assert fact.maturity == Maturity.EXPERIMENTAL
            assert "MATCH" in fact.cypher_query
            assert "RETURN" in fact.cypher_query
            assert fact.cypher_visual_query.strip().split()[0] in {"MATCH", "WITH"}
            assert "COUNT" in fact.cypher_count_query

    assert len(nist_ai_third_party_app_inventory.facts) == 1
    assert len(nist_ai_third_party_app_sensitive_scopes.facts) == 1
    assert len(nist_ai_admin_ai_app_authorizations.facts) == 1
    assert len(nist_ai_provider_api_key_hygiene.facts) == 2


def test_nist_ai_framework_requirements():
    inventory_requirements = {
        fw.requirement for fw in nist_ai_third_party_app_inventory.frameworks
    }
    sensitive_requirements = {
        fw.requirement for fw in nist_ai_third_party_app_sensitive_scopes.frameworks
    }
    admin_requirements = {
        fw.requirement for fw in nist_ai_admin_ai_app_authorizations.frameworks
    }
    provider_requirements = {
        fw.requirement for fw in nist_ai_provider_api_key_hygiene.frameworks
    }

    assert inventory_requirements == {"map 1"}
    assert sensitive_requirements == {"measure 2", "manage 2"}
    assert admin_requirements == {"govern 5"}
    assert provider_requirements == {"govern 5", "manage 2"}


def test_nist_ai_parse_results_preserves_extra_fields():
    fact = nist_ai_third_party_app_inventory.get_fact_by_id(
        "cross_cloud_nist_ai_app_inventory"
    )
    sample_results = [
        {
            "app_name": "OpenAI",
            "app_client_id": "client-1",
            "app_source": "googleworkspace",
            "match_method": "allowlist",
            "authorized_identity_count": 10,
            "authorization_event_count": 12,
            "debug_signal": "extra context",
        }
    ]

    findings = nist_ai_third_party_app_inventory.parse_results(fact, sample_results)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.app_name == "OpenAI"
    assert finding.app_client_id == "client-1"
    assert finding.authorized_identity_count == 10
    assert finding.authorization_event_count == 12
    assert finding.source == Module.CROSS_CLOUD.value
    assert finding.extra["debug_signal"] == "extra context"
