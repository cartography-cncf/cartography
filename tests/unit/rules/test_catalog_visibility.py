from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.cis_aws_iam import cis_aws_2_11_unused_credentials
from cartography.rules.data.rules.cis_aws_iam import cis_aws_2_13_access_key_not_rotated
from cartography.rules.data.rules.guardduty_active_threat import guardduty_active_threat
from cartography.rules.data.rules.nist_ai_rmf import nist_ai_admin_ai_app_authorizations
from cartography.rules.data.rules.nist_ai_rmf import nist_ai_aibom_agent_inventory
from cartography.rules.data.rules.nist_ai_rmf import nist_ai_aibom_coverage_gaps
from cartography.rules.data.rules.nist_ai_rmf import nist_ai_provider_api_key_hygiene
from cartography.rules.data.rules.nist_ai_rmf import nist_ai_third_party_app_inventory
from cartography.rules.data.rules.nist_ai_rmf import (
    nist_ai_third_party_app_sensitive_scopes,
)
from cartography.rules.data.rules.object_storage_public import object_storage_public
from cartography.rules.data.rules.subimage_coverage import aws_account_not_synced
from cartography.rules.data.rules.subimage_coverage import container_image_not_found
from cartography.rules.formatters import to_serializable
from cartography.rules.runners import get_all_frameworks
from cartography.rules.spec.model import Catalog
from cartography.rules.spec.result import CounterResult
from cartography.rules.spec.result import RuleResult


def _serialized_catalog_visibility(rule) -> list[str]:
    result = RuleResult(
        rule_id=rule.id,
        rule_name=rule.name,
        rule_description=rule.description,
        counter=CounterResult(),
        rule_tags=rule.tags,
        rule_frameworks=rule.frameworks,
        rule_catalog_visibility=rule.catalog_visibility,
    )
    return to_serializable(result)["rule_catalog_visibility"]


def test_cis_catalog_rules_are_compliance_only() -> None:
    cis_rules = {
        rule_id: rule
        for rule_id, rule in RULES.items()
        if rule_id.startswith(("cis_aws_", "cis_gcp_", "cis_k8s_", "cis_gw_"))
    }

    assert cis_rules
    for rule in cis_rules.values():
        assert rule.catalog_visibility == (Catalog.COMPLIANCE,)

    assert _serialized_catalog_visibility(cis_aws_2_11_unused_credentials) == [
        "compliance"
    ]
    assert _serialized_catalog_visibility(cis_aws_2_13_access_key_not_rotated) == [
        "compliance"
    ]


def test_standalone_operational_rules_serialize_as_rules() -> None:
    for rule in (
        guardduty_active_threat,
        container_image_not_found,
        aws_account_not_synced,
    ):
        assert rule.frameworks == ()
        assert rule.catalog_visibility == (Catalog.RULES,)
        assert _serialized_catalog_visibility(rule) == ["rules"]


def test_framework_mapped_operational_rules_serialize_as_rules_and_compliance() -> None:
    assert object_storage_public.frameworks
    assert object_storage_public.catalog_visibility == (
        Catalog.RULES,
        Catalog.COMPLIANCE,
    )
    assert _serialized_catalog_visibility(object_storage_public) == [
        "rules",
        "compliance",
    ]


def test_nist_ai_rmf_operational_rules_serialize_as_rules_and_compliance() -> None:
    for rule in (
        nist_ai_third_party_app_inventory,
        nist_ai_third_party_app_sensitive_scopes,
        nist_ai_admin_ai_app_authorizations,
        nist_ai_aibom_agent_inventory,
        nist_ai_aibom_coverage_gaps,
        nist_ai_provider_api_key_hygiene,
    ):
        assert rule.has_framework("nist-ai-rmf", revision="1.0")
        assert rule.catalog_visibility == (Catalog.RULES, Catalog.COMPLIANCE)
        assert _serialized_catalog_visibility(rule) == ["rules", "compliance"]


def test_catalog_visibility_does_not_remove_framework_mappings() -> None:
    assert cis_aws_2_11_unused_credentials.has_framework("cis", "aws", "6.0.0")
    assert cis_aws_2_11_unused_credentials.has_framework("27001", revision="2022")

    frameworks = get_all_frameworks()
    cis_aws_rules = [
        rule for rule in RULES.values() if rule.has_framework("cis", "aws", "6.0.0")
    ]
    assert "cis" in frameworks
    assert len(cis_aws_rules) == 18
