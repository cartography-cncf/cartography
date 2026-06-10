import re
from pathlib import Path

from cartography.rules.data.rules import RULES
from cartography.rules.formatters import to_serializable
from cartography.rules.runners import filter_rules_by_framework
from cartography.rules.spec.result import CounterResult
from cartography.rules.spec.result import RuleResult

RULE_DATA_DIR = Path(__file__).parents[3] / "cartography" / "rules" / "data" / "rules"

COMPLIANCE_NAME_PREFIX = re.compile(
    r"^(CIS AWS|CIS GCP|CIS Google Workspace|CIS Kubernetes|CIS K8s|NIST AI RMF)\b"
)
HELPER_CONTROL_TITLE_ARG = re.compile(
    r"\b("
    r"cis_aws|cis_gcp|cis_google_workspace|cis_kubernetes|"
    r"iso27001_annex_a|nist_ai_rmf"
    r")\([^)]*\bcontrol_title\s*=",
    re.DOTALL,
)
# Rule files should use central helper defaults for known framework control titles.
# If a helper's default title is intentionally wrong for a specific mapping, add
# the file name and helper name here before passing control_title= in that rule.
ALLOWED_HELPER_CONTROL_TITLE_OVERRIDES: dict[str, set[str]] = {}


def test_rule_ids_do_not_use_compliance_prefixes():
    for rule in RULES.values():
        assert not rule.id.startswith(("cis_", "nist_ai_")), rule.id


def test_rule_names_do_not_use_compliance_control_prefixes():
    for rule in RULES.values():
        assert not COMPLIANCE_NAME_PREFIX.match(rule.name), rule.name


def test_rule_framework_mappings_have_control_titles():
    for rule in RULES.values():
        for framework in rule.frameworks:
            assert framework.control_title is not None, (rule.id, framework)


def test_rule_definitions_use_framework_helper_default_control_titles():
    for path in RULE_DATA_DIR.glob("*.py"):
        allowed_helpers = ALLOWED_HELPER_CONTROL_TITLE_OVERRIDES.get(path.name, set())
        inline_helpers = {
            match.group(1)
            for match in HELPER_CONTROL_TITLE_ARG.finditer(path.read_text())
        }
        assert inline_helpers - allowed_helpers == set(), str(path)


def test_multiple_rules_can_map_to_same_framework_control():
    mappings: dict[tuple[str, str | None, str | None, str, str | None], set[str]] = {}
    for rule in RULES.values():
        for framework in rule.frameworks:
            key = (
                framework.short_name,
                framework.scope,
                framework.revision,
                framework.requirement,
                framework.control_title,
            )
            mappings.setdefault(key, set()).add(rule.id)

    privileged_access_rights = (
        "iso",
        "27001",
        "2022",
        "8.2",
        "Privileged access rights",
    )
    assert {
        "identity_administration_privileges",
        "policy_administration_privileges",
        "kubernetes_bind_impersonate_escalate_permissions",
    }.issubset(mappings[privileged_access_rights])


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
            "nist",
            "ai-rmf",
            "1.0",
            "govern 5",
            "Processes are in place for robust engagement with relevant AI actors",
        ),
    }

    for rule_id, (
        short_name,
        scope,
        revision,
        requirement,
        control_title,
    ) in expected.items():
        rule = RULES[rule_id]
        assert any(
            fw.short_name == short_name
            and fw.scope == scope
            and fw.revision == revision
            and fw.requirement == requirement
            and fw.control_title == control_title
            for fw in rule.frameworks
        )


def test_rule_name_and_framework_control_title_can_differ():
    rule = RULES["kubernetes_bind_impersonate_escalate_permissions"]
    fw = next(
        fw
        for fw in rule.frameworks
        if fw.short_name == "cis" and fw.requirement == "5.1.8"
    )

    assert rule.name == "Bind/Impersonate/Escalate Permissions"
    assert (
        fw.control_title
        == "Limit use of the Bind, Impersonate and Escalate permissions in the Kubernetes cluster"
    )
    assert rule.name != fw.control_title


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
        "NIST:ai-rmf",
    )
    assert "aws_root_user_access_keys" in filter_rules_by_framework(
        rule_ids,
        "iso:27001",
    )
    assert "aws_root_user_access_keys" in filter_rules_by_framework(
        rule_ids,
        "iso:27001:2022",
    )
    assert "aws_root_user_access_keys" in filter_rules_by_framework(
        rule_ids,
        "ISO27001",
    )
    assert "ai_provider_api_key_hygiene" in filter_rules_by_framework(
        rule_ids,
        "NIST-AI-RMF",
    )


def test_framework_control_title_is_serialized_in_rule_results():
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
        cis_framework["control_title"]
        == "Limit use of the Bind, Impersonate and Escalate permissions in the Kubernetes cluster"
    )
    assert "title" not in cis_framework
