import re

from cartography.rules.data.rules import RULES
from cartography.rules.formatters import to_serializable
from cartography.rules.runners import filter_rules_by_framework
from cartography.rules.spec.result import CounterResult
from cartography.rules.spec.result import RuleResult

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
        "aws_cloudtrail_multi_region": (
            "cis",
            "aws",
            "6.0.0",
            "4.1",
            "Ensure CloudTrail is enabled in all regions",
        ),
        "aws_default_security_group_restricts_traffic": (
            "cis",
            "aws",
            "6.0.0",
            "6.5",
            "Ensure the default security group of every VPC restricts all traffic",
        ),
        "gcp_projects_without_effective_os_login": (
            "cis",
            "gcp",
            "4.0",
            "4.4",
            "Ensure Oslogin Is Enabled for a Project",
        ),
        "kubernetes_pods_sharing_host_pid_namespace": (
            "cis",
            "kubernetes",
            "1.12",
            "5.2.3",
            "Minimize the admission of containers wishing to share the host process ID namespace",
        ),
        "kubernetes_bind_impersonate_escalate_permissions": (
            "cis",
            "kubernetes",
            "1.12",
            "5.1.8",
            "Limit use of the Bind, Impersonate and Escalate permissions in the Kubernetes cluster",
        ),
        "ai_provider_api_key_hygiene": (
            "nist-ai-rmf",
            None,
            "1.0",
            "govern 5",
            "Organizational teams are committed to a culture that considers and communicates AI risk",
        ),
    }

    for rule_id, (short_name, scope, revision, requirement, title) in expected.items():
        rule = RULES[rule_id]
        assert any(
            fw.short_name == short_name
            and fw.scope == scope
            and fw.revision == revision
            and fw.requirement == requirement
            and fw.title == title
            for fw in rule.frameworks
        )


def test_rule_name_and_framework_title_can_differ():
    rule = RULES["kubernetes_bind_impersonate_escalate_permissions"]
    fw = next(
        fw
        for fw in rule.frameworks
        if fw.short_name == "cis" and fw.requirement == "5.1.8"
    )

    assert rule.name == "Bind/Impersonate/Escalate Permissions"
    assert (
        fw.title
        == "Limit use of the Bind, Impersonate and Escalate permissions in the Kubernetes cluster"
    )
    assert rule.name != fw.title


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


def test_framework_title_is_serialized_in_rule_results():
    rule = RULES["kubernetes_bind_impersonate_escalate_permissions"]
    result = RuleResult(
        rule_id=rule.id,
        rule_name=rule.name,
        rule_description=rule.description,
        counter=CounterResult(),
        rule_frameworks=rule.frameworks,
    )

    serialized = to_serializable(result)
    cis_framework = next(
        fw
        for fw in serialized["rule_frameworks"]
        if fw["short_name"] == "cis" and fw["requirement"] == "5.1.8"
    )

    assert (
        cis_framework["title"]
        == "Limit use of the Bind, Impersonate and Escalate permissions in the Kubernetes cluster"
    )
