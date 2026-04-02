from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.nist_ai_rmf import nist_ai_admin_ai_app_authorizations
from cartography.rules.data.rules.nist_ai_rmf import nist_ai_aibom_agent_inventory
from cartography.rules.data.rules.nist_ai_rmf import nist_ai_aibom_coverage_gaps
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
        "nist_ai_aibom_agent_inventory": nist_ai_aibom_agent_inventory,
        "nist_ai_aibom_coverage_gaps": nist_ai_aibom_coverage_gaps,
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
    assert nist_ai_aibom_agent_inventory.modules == {Module.AIBOM}
    assert nist_ai_aibom_coverage_gaps.modules == {Module.AIBOM}
    assert nist_ai_provider_api_key_hygiene.modules == {Module.OPENAI, Module.ANTHROPIC}


def test_nist_ai_fact_structure_and_maturity():
    rules = (
        nist_ai_third_party_app_inventory,
        nist_ai_third_party_app_sensitive_scopes,
        nist_ai_admin_ai_app_authorizations,
        nist_ai_aibom_agent_inventory,
        nist_ai_aibom_coverage_gaps,
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
    assert len(nist_ai_aibom_agent_inventory.facts) == 1
    assert len(nist_ai_aibom_coverage_gaps.facts) == 1
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
    aibom_inventory_requirements = {
        fw.requirement for fw in nist_ai_aibom_agent_inventory.frameworks
    }
    aibom_gap_requirements = {
        fw.requirement for fw in nist_ai_aibom_coverage_gaps.frameworks
    }
    provider_requirements = {
        fw.requirement for fw in nist_ai_provider_api_key_hygiene.frameworks
    }

    assert inventory_requirements == {"map 1"}
    assert sensitive_requirements == {"measure 2", "manage 2"}
    assert admin_requirements == {"govern 5"}
    assert aibom_inventory_requirements == {"map 1", "govern 1"}
    assert aibom_gap_requirements == {"measure 2", "manage 2"}
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


def test_nist_ai_aibom_parse_results_preserves_lists_and_extra_fields():
    fact = nist_ai_aibom_agent_inventory.get_fact_by_id("aibom_nist_ai_agent_inventory")
    sample_results = [
        {
            "source_id": "source-1",
            "image_uri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/example@sha256:abc",
            "manifest_digest": "sha256:abc",
            "agent_component_id": "agent-1",
            "agent_name": "pydantic_ai.Agent",
            "tool_count": 1,
            "tool_names": ["fetch_customer_profile"],
            "traceability_note": "captured from AIBOM",
        }
    ]

    findings = nist_ai_aibom_agent_inventory.parse_results(fact, sample_results)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.agent_component_id == "agent-1"
    assert finding.agent_name == "pydantic_ai.Agent"
    assert finding.tool_count == 1
    assert finding.tool_names == ["fetch_customer_profile"]
    assert finding.source == Module.AIBOM.value
    assert finding.extra["traceability_note"] == "captured from AIBOM"


def test_nist_ai_admin_ai_app_authorizations_count_query_counts_distinct_apps():
    fact = nist_ai_admin_ai_app_authorizations.get_fact_by_id(
        "gw_nist_ai_admin_app_authorizations"
    )

    assert "RETURN COUNT(DISTINCT app) AS count" in fact.cypher_count_query


def test_nist_ai_openai_api_key_query_avoids_invalid_grouping_expression():
    fact = nist_ai_provider_api_key_hygiene.get_fact_by_id(
        "openai_nist_ai_stale_or_unowned_api_keys"
    )

    assert "has_user_owner, count(sa) > 0 AS has_sa_owner" in fact.cypher_query
    assert "has_user_owner OR has_sa_owner AS has_owner" in fact.cypher_query


def test_nist_ai_openai_api_key_query_includes_project_scoped_keys():
    fact = nist_ai_provider_api_key_hygiene.get_fact_by_id(
        "openai_nist_ai_stale_or_unowned_api_keys"
    )

    assert "MATCH (k)" in fact.cypher_query
    assert (
        "OPTIONAL MATCH (project:OpenAIProject)-[:RESOURCE]->(k)" in fact.cypher_query
    )
    assert (
        "OPTIONAL MATCH (org_from_project:OpenAIOrganization)-[:RESOURCE]->(project)"
        in fact.cypher_query
    )
    assert "coalesce(org_from_project, org_direct) AS org" in fact.cypher_query
    assert (
        "OPTIONAL MATCH p4=(org_from_project:OpenAIOrganization)-[:RESOURCE]->(project)"
        in fact.cypher_visual_query
    )


def test_nist_ai_aibom_coverage_gap_count_query_counts_all_sources():
    fact = nist_ai_aibom_coverage_gaps.get_fact_by_id("aibom_nist_ai_coverage_gaps")

    assert fact.cypher_count_query.strip() == (
        "MATCH (source:AIBOMSource)\n" "    RETURN COUNT(source) AS count"
    )


def test_nist_ai_aibom_agent_inventory_stages_embedding_aggregation():
    fact = nist_ai_aibom_agent_inventory.get_fact_by_id("aibom_nist_ai_agent_inventory")

    assert "OPTIONAL MATCH (agent)-[:USES_EMBEDDING]->(embedding:AIEmbedding)" in (
        fact.cypher_query
    )
    assert "count(DISTINCT embedding) AS embedding_count" in fact.cypher_query
    assert "collect(DISTINCT embedding.name) AS embedding_names" in fact.cypher_query
    assert "embedding_count,\n        embedding_names" in fact.cypher_query
