"""
Unit tests for CIS Kubernetes Benchmark rules.

Tests validate that rules are properly structured and that
framework metadata is correctly configured.
"""

import pytest

from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_1_cluster_admin_usage,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_2_secret_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_3_wildcard_roles,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_4_pod_create_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_5_default_sa_bindings,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_7_system_masters_group,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_8_escalation_permissions,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_9_pv_create_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_10_node_proxy_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_11_csr_approval_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_12_webhook_config_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    cis_k8s_5_1_13_sa_token_creation,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    cis_k8s_5_4_1_secrets_in_env_vars,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    cis_k8s_5_6_4_default_namespace,
)
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module

ALL_CIS_K8S_RULES = [
    cis_k8s_5_1_1_cluster_admin_usage,
    cis_k8s_5_1_2_secret_access,
    cis_k8s_5_1_3_wildcard_roles,
    cis_k8s_5_1_4_pod_create_access,
    cis_k8s_5_1_5_default_sa_bindings,
    cis_k8s_5_1_7_system_masters_group,
    cis_k8s_5_1_8_escalation_permissions,
    cis_k8s_5_1_9_pv_create_access,
    cis_k8s_5_1_10_node_proxy_access,
    cis_k8s_5_1_11_csr_approval_access,
    cis_k8s_5_1_12_webhook_config_access,
    cis_k8s_5_1_13_sa_token_creation,
    cis_k8s_5_4_1_secrets_in_env_vars,
    cis_k8s_5_6_4_default_namespace,
]


class TestCisKubernetesRuleStructure:
    """Test that all CIS Kubernetes rules have proper structure."""

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_rule_has_unique_id(self, rule):
        assert rule.id is not None
        assert len(rule.id) > 0
        assert rule.id.startswith("cis_k8s_")

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_rule_has_name_and_description(self, rule):
        assert rule.name is not None
        assert len(rule.name) > 0
        assert rule.description is not None
        assert len(rule.description) > 0

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_rule_has_at_least_one_fact(self, rule):
        assert len(rule.facts) >= 1

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_rule_has_tags(self, rule):
        assert len(rule.tags) >= 1

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_rule_has_output_model(self, rule):
        assert rule.output_model is not None

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_rule_has_references(self, rule):
        assert len(rule.references) >= 1


class TestCisKubernetesFrameworkMetadata:
    """Test that all CIS Kubernetes rules have correct framework metadata."""

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_rule_has_cis_framework(self, rule):
        assert len(rule.frameworks) == 1
        fw = rule.frameworks[0]
        assert fw.short_name == "cis"
        assert fw.scope == "kubernetes"
        assert fw.revision == "1.12"

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_rule_has_valid_requirement(self, rule):
        fw = rule.frameworks[0]
        assert fw.requirement is not None
        assert fw.requirement.startswith("5.")

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_rule_matches_cis_kubernetes_filter(self, rule):
        assert rule.has_framework(short_name="CIS", scope="kubernetes")
        assert rule.has_framework(short_name="CIS", scope="kubernetes", revision="1.12")

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_rule_does_not_match_other_scopes(self, rule):
        assert not rule.has_framework(short_name="CIS", scope="aws")
        assert not rule.has_framework(short_name="CIS", scope="gcp")


class TestCisKubernetesFactMetadata:
    """Test that all facts have correct metadata."""

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_all_facts_use_kubernetes_module(self, rule):
        for fact in rule.facts:
            assert fact.module == Module.KUBERNETES

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_all_facts_are_experimental(self, rule):
        for fact in rule.facts:
            assert fact.maturity == Maturity.EXPERIMENTAL

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_all_facts_have_cypher_queries(self, rule):
        for fact in rule.facts:
            assert fact.cypher_query is not None
            assert len(fact.cypher_query.strip()) > 0
            assert fact.cypher_visual_query is not None
            assert len(fact.cypher_visual_query.strip()) > 0
            assert fact.cypher_count_query is not None
            assert len(fact.cypher_count_query.strip()) > 0

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_all_facts_have_unique_ids(self, rule):
        fact_ids = [fact.id for fact in rule.facts]
        assert len(fact_ids) == len(set(fact_ids))

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_count_queries_return_count(self, rule):
        for fact in rule.facts:
            assert "COUNT" in fact.cypher_count_query
            assert "AS count" in fact.cypher_count_query


class TestCisKubernetesRuleRegistration:
    """Test that all rules are registered in the RULES dict."""

    def test_all_rules_registered(self):
        from cartography.rules.data.rules import RULES

        for rule in ALL_CIS_K8S_RULES:
            assert rule.id in RULES, f"Rule {rule.id} not found in RULES registry"
            assert RULES[rule.id] is rule

    def test_rule_count(self):
        from cartography.rules.data.rules import RULES

        k8s_rules = {
            k: v for k, v in RULES.items() if k.startswith("cis_k8s_")
        }
        assert len(k8s_rules) == 14


class TestCisKubernetesRuleIds:
    """Test that rule IDs follow the expected convention."""

    EXPECTED_RULES = {
        "cis_k8s_5_1_1_cluster_admin_usage": "5.1.1",
        "cis_k8s_5_1_2_secret_access": "5.1.2",
        "cis_k8s_5_1_3_wildcard_roles": "5.1.3",
        "cis_k8s_5_1_4_pod_create_access": "5.1.4",
        "cis_k8s_5_1_5_default_sa_bindings": "5.1.5",
        "cis_k8s_5_1_7_system_masters_group": "5.1.7",
        "cis_k8s_5_1_8_escalation_permissions": "5.1.8",
        "cis_k8s_5_1_9_pv_create_access": "5.1.9",
        "cis_k8s_5_1_10_node_proxy_access": "5.1.10",
        "cis_k8s_5_1_11_csr_approval_access": "5.1.11",
        "cis_k8s_5_1_12_webhook_config_access": "5.1.12",
        "cis_k8s_5_1_13_sa_token_creation": "5.1.13",
        "cis_k8s_5_4_1_secrets_in_env_vars": "5.4.1",
        "cis_k8s_5_6_4_default_namespace": "5.6.4",
    }

    def test_all_expected_rules_exist(self):
        rule_ids = {r.id for r in ALL_CIS_K8S_RULES}
        for expected_id in self.EXPECTED_RULES:
            assert expected_id in rule_ids, f"Expected rule {expected_id} not found"

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_rule_id_matches_framework_requirement(self, rule):
        expected_requirement = self.EXPECTED_RULES.get(rule.id)
        assert expected_requirement is not None, f"Unknown rule {rule.id}"
        fw = rule.frameworks[0]
        assert fw.requirement == expected_requirement
