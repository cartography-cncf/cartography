"""
Unit tests for CIS Kubernetes Benchmark rules.

Tests validate that rules are properly structured and that
framework metadata is correctly configured.
"""

import pytest

from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_bind_impersonate_escalate_permissions,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_cluster_admin_role_usage,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_csr_approval_subresource_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_default_service_account_bindings,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_node_proxy_subresource_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_roles_grant_persistent_volume_creation,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_roles_grant_pod_creation,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_roles_grant_secret_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_service_account_token_creation_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_system_masters_group_usage,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import (
    kubernetes_webhook_configuration_access,
)
from cartography.rules.data.rules.cis_kubernetes_rbac import kubernetes_wildcard_roles
from cartography.rules.data.rules.cis_kubernetes_workloads import _cypher_string_list
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_containers_allowing_privilege_escalation,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_containers_using_hostports,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_pods_missing_runtime_default_seccomp,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_pods_running_in_default_namespace,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_pods_sharing_host_ipc_namespace,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_pods_sharing_host_network_namespace,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_pods_sharing_host_pid_namespace,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_pods_using_hostpath_volumes,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_secrets_used_as_environment_variables,
)
from cartography.rules.data.rules.cis_kubernetes_workloads import (
    kubernetes_service_account_tokens_mounted_in_pods,
)
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module

ALL_CIS_K8S_RULES = [
    kubernetes_cluster_admin_role_usage,
    kubernetes_roles_grant_secret_access,
    kubernetes_wildcard_roles,
    kubernetes_roles_grant_pod_creation,
    kubernetes_default_service_account_bindings,
    kubernetes_system_masters_group_usage,
    kubernetes_bind_impersonate_escalate_permissions,
    kubernetes_roles_grant_persistent_volume_creation,
    kubernetes_node_proxy_subresource_access,
    kubernetes_csr_approval_subresource_access,
    kubernetes_webhook_configuration_access,
    kubernetes_service_account_token_creation_access,
    kubernetes_service_account_tokens_mounted_in_pods,
    kubernetes_pods_sharing_host_pid_namespace,
    kubernetes_pods_sharing_host_ipc_namespace,
    kubernetes_pods_sharing_host_network_namespace,
    kubernetes_containers_allowing_privilege_escalation,
    kubernetes_pods_using_hostpath_volumes,
    kubernetes_containers_using_hostports,
    kubernetes_secrets_used_as_environment_variables,
    kubernetes_pods_missing_runtime_default_seccomp,
    kubernetes_pods_running_in_default_namespace,
]


class TestCisKubernetesRuleStructure:
    """Test that all CIS Kubernetes rules have proper structure."""

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_rule_has_unique_id(self, rule):
        assert rule.id is not None
        assert len(rule.id) > 0
        assert rule.id.startswith("kubernetes_")

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
        fw = next(
            fw
            for fw in rule.frameworks
            if fw.short_name == "cis" and fw.scope == "kubernetes"
        )
        assert fw.short_name == "cis"
        assert fw.scope == "kubernetes"
        assert fw.revision == "1.12"

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_rule_has_valid_requirement(self, rule):
        fw = next(
            fw
            for fw in rule.frameworks
            if fw.short_name == "cis" and fw.scope == "kubernetes"
        )
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


class TestCisKubernetesServiceAccountTokenMounts:
    """Test CIS Kubernetes 5.1.6 service account token mount query behavior."""

    def test_service_account_token_mounts_excludes_infrastructure_namespaces(
        self,
    ):
        fact = kubernetes_service_account_tokens_mounted_in_pods.facts[0]

        assert "service_account_namespace IN" in fact.cypher_query
        assert '"kube-system"' in fact.cypher_query
        assert '"istio-system"' in fact.cypher_query
        assert '"cert-manager"' in fact.cypher_query
        assert '"calico-system"' in fact.cypher_query
        assert '"ingress-nginx"' in fact.cypher_query
        assert '"gatekeeper-system"' in fact.cypher_query
        assert '"kyverno"' in fact.cypher_query

    def test_service_account_token_mounts_excludes_infrastructure_service_accounts(
        self,
    ):
        fact = kubernetes_service_account_tokens_mounted_in_pods.facts[0]

        assert "service_account_name IN" in fact.cypher_query
        assert '"aws-load-balancer-controller"' in fact.cypher_query
        assert '"cluster-autoscaler"' in fact.cypher_query
        assert '"karpenter"' in fact.cypher_query
        assert '"metrics-server"' in fact.cypher_query
        assert '"vertical-pod-autoscaler-recommender"' in fact.cypher_query

    def test_service_account_token_mounts_excludes_irsa_mounts(self):
        fact = kubernetes_service_account_tokens_mounted_in_pods.facts[0]

        assert "sa.aws_role_arn IS NOT NULL" in fact.cypher_query
        assert "EXISTS { (sa)-[:ASSUMES_ROLE]->(:AWSRole) }" in fact.cypher_query
        assert "service_account_assumes_aws_role" in fact.cypher_query

    def test_service_account_token_mounts_excludes_gke_workload_identity_mounts(self):
        fact = kubernetes_service_account_tokens_mounted_in_pods.facts[0]

        assert "sa.gcp_service_account IS NOT NULL" in fact.cypher_query
        assert (
            "EXISTS { (sa)-[:WORKLOAD_IDENTITY_BINDING]->(:GCPServiceAccount) }"
            in fact.cypher_query
        )
        assert "service_account_assumes_gcp_identity" in fact.cypher_query

    def test_service_account_token_mounts_excludes_default_sa_mounts(self):
        fact = kubernetes_service_account_tokens_mounted_in_pods.facts[0]

        assert "service_account_name = 'default'" in fact.cypher_query

    def test_service_account_token_mounts_uses_ontology_service_account_name(self):
        fact = kubernetes_service_account_tokens_mounted_in_pods.facts[0]

        assert (
            "coalesce(sa._ont_name, sa.name, pod.service_account_name)"
            in fact.cypher_query
        )
        assert "service_account_name AS service_account_name" in fact.cypher_query

    def test_service_account_token_mounts_visual_query_matches_filter(self):
        fact = kubernetes_service_account_tokens_mounted_in_pods.facts[0]

        assert "service_account_name = 'default'" in fact.cypher_visual_query
        assert "service_account_namespace IN" in fact.cypher_visual_query
        assert "service_account_name IN" in fact.cypher_visual_query
        assert "service_account_assumes_aws_role" in fact.cypher_visual_query
        assert "service_account_assumes_gcp_identity" in fact.cypher_visual_query

    def test_service_account_token_mounts_count_query_matches_candidate_filter(self):
        fact = kubernetes_service_account_tokens_mounted_in_pods.facts[0]

        assert "service_account_name = 'default'" in fact.cypher_count_query
        assert "service_account_namespace IN" in fact.cypher_count_query
        assert "service_account_name IN" in fact.cypher_count_query
        assert "service_account_assumes_aws_role" in fact.cypher_count_query
        assert "service_account_assumes_gcp_identity" in fact.cypher_count_query
        assert "effective_automount = true" not in fact.cypher_count_query

    def test_cypher_string_list_escapes_values_for_double_quoted_literals(self):
        assert (
            _cypher_string_list(
                ("kube-system", "team's-controller", 'quote"controller')
            )
            == '["kube-system", "team\'s-controller", "quote\\"controller"]'
        )


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
            k: v
            for k, v in RULES.items()
            if v.has_framework(
                short_name="cis",
                scope="kubernetes",
                revision="1.12",
            )
        }
        assert len(k8s_rules) == 22


class TestCisKubernetesRuleIds:
    """Test that rule IDs follow the expected convention."""

    EXPECTED_RULES = {
        "kubernetes_cluster_admin_role_usage": "5.1.1",
        "kubernetes_roles_grant_secret_access": "5.1.2",
        "kubernetes_wildcard_roles": "5.1.3",
        "kubernetes_roles_grant_pod_creation": "5.1.4",
        "kubernetes_default_service_account_bindings": "5.1.5",
        "kubernetes_system_masters_group_usage": "5.1.7",
        "kubernetes_bind_impersonate_escalate_permissions": "5.1.8",
        "kubernetes_roles_grant_persistent_volume_creation": "5.1.9",
        "kubernetes_node_proxy_subresource_access": "5.1.10",
        "kubernetes_csr_approval_subresource_access": "5.1.11",
        "kubernetes_webhook_configuration_access": "5.1.12",
        "kubernetes_service_account_token_creation_access": "5.1.13",
        "kubernetes_service_account_tokens_mounted_in_pods": "5.1.6",
        "kubernetes_pods_sharing_host_pid_namespace": "5.2.3",
        "kubernetes_pods_sharing_host_ipc_namespace": "5.2.4",
        "kubernetes_pods_sharing_host_network_namespace": "5.2.5",
        "kubernetes_containers_allowing_privilege_escalation": "5.2.6",
        "kubernetes_pods_using_hostpath_volumes": "5.2.11",
        "kubernetes_containers_using_hostports": "5.2.12",
        "kubernetes_secrets_used_as_environment_variables": "5.4.1",
        "kubernetes_pods_missing_runtime_default_seccomp": "5.6.2",
        "kubernetes_pods_running_in_default_namespace": "5.6.4",
    }

    def test_all_expected_rules_exist(self):
        rule_ids = {r.id for r in ALL_CIS_K8S_RULES}
        for expected_id in self.EXPECTED_RULES:
            assert expected_id in rule_ids, f"Expected rule {expected_id} not found"

    @pytest.mark.parametrize("rule", ALL_CIS_K8S_RULES, ids=lambda r: r.id)
    def test_rule_id_matches_framework_requirement(self, rule):
        expected_requirement = self.EXPECTED_RULES.get(rule.id)
        assert expected_requirement is not None, f"Unknown rule {rule.id}"
        fw = next(
            fw
            for fw in rule.frameworks
            if fw.short_name == "cis" and fw.scope == "kubernetes"
        )
        assert fw.requirement == expected_requirement
