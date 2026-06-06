from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.cis_aws_iam import cis_aws_2_11_unused_credentials
from cartography.rules.data.rules.cis_aws_iam import cis_aws_2_13_access_key_not_rotated
from cartography.rules.data.rules.cis_aws_networking import (
    cis_aws_6_3_remote_admin_ipv4,
)
from cartography.rules.data.rules.cis_aws_storage import (
    cis_aws_3_1_4_s3_block_public_access,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    cis_k8s_5_6_2_runtime_default_seccomp,
)
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
from cartography.rules.spec.result import CounterResult
from cartography.rules.spec.result import RuleResult


def _serialized_compliance_only(rule) -> bool:
    result = RuleResult(
        rule_id=rule.id,
        rule_name=rule.name,
        rule_description=rule.description,
        counter=CounterResult(),
        rule_tags=rule.tags,
        rule_frameworks=rule.frameworks,
        rule_compliance_only=rule.compliance_only,
    )
    return to_serializable(result)["rule_compliance_only"]


def test_framework_prefixed_rules_are_compliance_only() -> None:
    for rule in (
        cis_aws_2_11_unused_credentials,
        cis_aws_2_13_access_key_not_rotated,
        cis_k8s_5_6_2_runtime_default_seccomp,
        cis_aws_6_3_remote_admin_ipv4,
        cis_aws_3_1_4_s3_block_public_access,
        nist_ai_provider_api_key_hygiene,
    ):
        assert rule.frameworks
        assert rule.compliance_only is True
        assert _serialized_compliance_only(rule) is True


def test_standalone_operational_rules_are_not_compliance_only() -> None:
    for rule in (
        guardduty_active_threat,
        container_image_not_found,
        aws_account_not_synced,
    ):
        assert rule.frameworks == ()
        assert rule.compliance_only is False
        assert _serialized_compliance_only(rule) is False


def test_framework_mapped_operational_rules_are_not_compliance_only() -> None:
    assert object_storage_public.frameworks
    assert object_storage_public.compliance_only is False
    assert _serialized_compliance_only(object_storage_public) is False


def test_all_framework_prefixed_rules_are_compliance_only() -> None:
    prefixed_rules = [
        rule for rule in RULES.values() if rule.id.startswith(("cis_", "nist_ai_"))
    ]

    assert prefixed_rules
    assert all(rule.compliance_only for rule in prefixed_rules)


def test_nist_ai_rmf_prefixed_rules_are_compliance_only() -> None:
    for rule in (
        nist_ai_third_party_app_inventory,
        nist_ai_third_party_app_sensitive_scopes,
        nist_ai_admin_ai_app_authorizations,
        nist_ai_aibom_agent_inventory,
        nist_ai_aibom_coverage_gaps,
        nist_ai_provider_api_key_hygiene,
    ):
        assert rule.has_framework("nist-ai-rmf", revision="1.0")
        assert rule.compliance_only is True
        assert _serialized_compliance_only(rule) is True


def test_compliance_only_does_not_remove_framework_mappings() -> None:
    assert cis_aws_2_11_unused_credentials.has_framework("cis", "aws", "6.0.0")
    assert cis_aws_2_11_unused_credentials.has_framework("27001", revision="2022")

    frameworks = get_all_frameworks()
    cis_aws_rules = [
        rule for rule in RULES.values() if rule.has_framework("cis", "aws", "6.0.0")
    ]
    assert "cis" in frameworks
    assert cis_aws_rules
