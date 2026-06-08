import re

from cartography.rules.data.rules import RULES
from cartography.rules.runners import filter_rules_by_framework

COMPLIANCE_NAME_PREFIX = re.compile(
    r"^(CIS AWS|CIS GCP|CIS Google Workspace|CIS Kubernetes|CIS K8s|NIST AI RMF)\b"
)


def test_rule_ids_do_not_use_compliance_prefixes():
    for rule in RULES.values():
        assert not rule.id.startswith(("cis_", "nist_ai_")), rule.id


def test_rule_names_do_not_use_compliance_control_prefixes():
    for rule in RULES.values():
        assert not COMPLIANCE_NAME_PREFIX.match(rule.name), rule.name


def test_framework_mappings_remain_on_renamed_rules():
    expected = {
        "aws_cloudtrail_multi_region": ("cis", "aws", "6.0.0", "4.1"),
        "aws_default_security_group_restricts_traffic": (
            "cis",
            "aws",
            "6.0.0",
            "6.5",
        ),
        "gcp_projects_without_effective_os_login": ("cis", "gcp", "4.0", "4.4"),
        "kubernetes_pods_sharing_host_pid_namespace": (
            "cis",
            "kubernetes",
            "1.12",
            "5.2.3",
        ),
        "ai_provider_api_key_hygiene": ("nist-ai-rmf", None, "1.0", "govern 5"),
    }

    for rule_id, (short_name, scope, revision, requirement) in expected.items():
        rule = RULES[rule_id]
        assert any(
            fw.short_name == short_name
            and fw.scope == scope
            and fw.revision == revision
            and fw.requirement == requirement
            for fw in rule.frameworks
        )


def test_framework_filtering_returns_renamed_rule_ids():
    rule_ids = list(RULES)

    assert "aws_cloudtrail_multi_region" in filter_rules_by_framework(
        rule_ids,
        "CIS:aws:6.0.0",
    )
    assert "gcp_projects_without_effective_os_login" in filter_rules_by_framework(
        rule_ids,
        "CIS:gcp:4.0",
    )
    assert "kubernetes_pods_sharing_host_pid_namespace" in filter_rules_by_framework(
        rule_ids, "CIS:kubernetes:1.12"
    )
    assert "ai_provider_api_key_hygiene" in filter_rules_by_framework(
        rule_ids,
        "NIST-AI-RMF",
    )
