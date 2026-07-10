import json
import logging
from typing import Any

import neo4j
from kubernetes.client.exceptions import ApiException
from kubernetes.client.models import V1LabelSelector
from kubernetes.client.models import V1NetworkPolicy
from kubernetes.client.models import V1NetworkPolicyEgressRule
from kubernetes.client.models import V1NetworkPolicyIngressRule
from kubernetes.client.models import V1NetworkPolicyPeer
from kubernetes.client.models import V1NetworkPolicyPort
from kubernetes.client.models import V1NetworkPolicySpec

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.networkpolicies import KubernetesNetworkPolicySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_network_policies(client: K8sClient) -> list[V1NetworkPolicy]:
    items = k8s_paginate(
        client.networking.list_network_policy_for_all_namespaces,
        raise_on_forbidden=True,
    )
    return items


def _format_label_selector(selector: V1LabelSelector | None) -> dict[str, Any] | None:
    if selector is None:
        return None
    match_expressions = None
    if selector.match_expressions:
        match_expressions = [
            {
                "key": expr.key,
                "operator": expr.operator,
                "values": expr.values,
            }
            for expr in selector.match_expressions
        ]
    return {
        "match_labels": selector.match_labels,
        "match_expressions": match_expressions,
    }


def _format_ports(
    ports: list[V1NetworkPolicyPort] | None,
) -> list[dict[str, Any]] | None:
    if ports is None:
        return None
    return [
        {
            "port": port.port,
            "protocol": port.protocol,
            "end_port": port.end_port,
        }
        for port in ports
    ]


def _format_peers(
    peers: list[V1NetworkPolicyPeer] | None,
) -> list[dict[str, Any]] | None:
    if peers is None:
        return None
    formatted_peers = []
    for peer in peers:
        ip_block = None
        if peer.ip_block:
            ip_block = {"cidr": peer.ip_block.cidr, "except": peer.ip_block._except}
        formatted_peers.append(
            {
                "ip_block": ip_block,
                "namespace_selector": _format_label_selector(peer.namespace_selector),
                "pod_selector": _format_label_selector(peer.pod_selector),
            }
        )
    return formatted_peers


def _format_ingress_rules(
    rules: list[V1NetworkPolicyIngressRule] | None,
) -> list[dict[str, Any]]:
    if rules is None:
        return []
    return [
        {
            "from": _format_peers(rule._from),
            "ports": _format_ports(rule.ports),
        }
        for rule in rules
    ]


def _format_egress_rules(
    rules: list[V1NetworkPolicyEgressRule] | None,
) -> list[dict[str, Any]]:
    if rules is None:
        return []
    return [
        {
            "to": _format_peers(rule.to),
            "ports": _format_ports(rule.ports),
        }
        for rule in rules
    ]


def _resolve_policy_types(spec: V1NetworkPolicySpec) -> list[str]:
    """
    Return the effective policyTypes for a NetworkPolicy. When spec.policy_types
    is unset, Kubernetes defaults it based on the rules present: Ingress always
    applies, and Egress applies when the policy has any egress rules. The
    apiserver usually populates this field on read, but the SDK model keeps it
    optional, so we apply the documented default explicitly rather than trusting
    it to be set.
    """
    if spec.policy_types is not None:
        return spec.policy_types
    policy_types = ["Ingress"]
    if spec.egress:
        policy_types.append("Egress")
    return policy_types


def _selector_matches(
    pod_labels: dict[str, str],
    match_labels: dict[str, str] | None,
    match_expressions: list[dict[str, Any]] | None,
) -> bool:
    """
    Evaluate a Kubernetes label selector against a pod's labels. A pod matches
    only if it satisfies every matchLabels entry AND every matchExpressions
    requirement (the selector terms are ANDed), following apimachinery semantics:
    In => label present and value in set; NotIn => label absent or value not in
    set; Exists => label present; DoesNotExist => label absent.
    """
    if match_labels:
        if not all(pod_labels.get(key) == value for key, value in match_labels.items()):
            return False

    for expr in match_expressions or []:
        key = expr["key"]
        operator = expr["operator"]
        values = expr.get("values") or []
        present = key in pod_labels
        value = pod_labels.get(key)
        if operator == "In":
            if not (present and value in values):
                return False
        elif operator == "NotIn":
            if present and value in values:
                return False
        elif operator == "Exists":
            if not present:
                return False
        elif operator == "DoesNotExist":
            if present:
                return False
        else:
            # Unknown operator: fail closed rather than silently over-matching.
            logger.warning(
                "Unknown NetworkPolicy matchExpressions operator %r; "
                "not matching this pod.",
                operator,
            )
            return False
    return True


def _match_pods(
    pod_selector: dict[str, Any] | None,
    namespace: str,
    all_pods: list[dict[str, Any]],
) -> list[str]:
    """
    Resolve a NetworkPolicy podSelector to the uids of the pods it selects, in
    the same namespace. An empty selector (no matchLabels and no
    matchExpressions) selects every pod in the namespace, per Kubernetes
    semantics; otherwise both equality-based matchLabels and set-based
    matchExpressions are evaluated (see _selector_matches).
    """
    selector = pod_selector or {}
    match_labels: dict[str, str] | None = selector.get("match_labels")
    match_expressions = selector.get("match_expressions")

    pod_ids = []
    for pod in all_pods:
        if pod["namespace"] != namespace:
            continue
        # Empty selector => selects all pods in the namespace.
        if not match_labels and not match_expressions:
            pod_ids.append(pod["uid"])
            continue
        pod_labels: dict[str, str] = json.loads(pod["labels"]) or {}
        if _selector_matches(pod_labels, match_labels, match_expressions):
            pod_ids.append(pod["uid"])
    return pod_ids


def transform_network_policies(
    policies: list[V1NetworkPolicy], all_pods: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    transformed_policies: list[dict[str, Any]] = []
    for policy in policies:
        namespace = policy.metadata.namespace
        policy_types = _resolve_policy_types(policy.spec)
        formatted_selector = _format_label_selector(policy.spec.pod_selector)

        transformed_policies.append(
            {
                "uid": policy.metadata.uid,
                "name": policy.metadata.name,
                "namespace": namespace,
                "creation_timestamp": get_epoch(policy.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(policy.metadata.deletion_timestamp),
                "pod_selector": json.dumps(formatted_selector),
                "policy_types": policy_types,
                "ingress_rules": json.dumps(_format_ingress_rules(policy.spec.ingress)),
                "egress_rules": json.dumps(_format_egress_rules(policy.spec.egress)),
                "restricts_ingress": "Ingress" in policy_types,
                "restricts_egress": "Egress" in policy_types,
                "pod_ids": _match_pods(formatted_selector, namespace, all_pods),
            }
        )
    return transformed_policies


def load_network_policies(
    session: neo4j.Session,
    network_policies: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    load(
        session,
        KubernetesNetworkPolicySchema(),
        network_policies,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


def cleanup(session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    logger.debug("Running cleanup job for KubernetesNetworkPolicy")
    cleanup_job = GraphJob.from_node_schema(
        KubernetesNetworkPolicySchema(), common_job_parameters
    )
    cleanup_job.run(session)


@timeit
def sync_network_policies(
    session: neo4j.Session,
    client: K8sClient,
    all_pods: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    try:
        policies = get_network_policies(client)
    except ApiException as e:
        if e.status in (401, 403):
            # Skipping load + cleanup is intentional: if the operator previously
            # granted `list networkpolicies` and later revoked it, running cleanup
            # would wipe the existing KubernetesNetworkPolicy subgraph for this
            # cluster and silently model every namespace as unsegmented.
            logger.warning(
                "Cartography lacks permission to list networkpolicies on cluster "
                "%s (status %s). Skipping NetworkPolicy sync and preserving "
                "previously synced policies. Grant `list networkpolicies` to the "
                "Cartography ClusterRole to enable this data.",
                client.name,
                e.status,
            )
            return
        raise
    transformed_policies = transform_network_policies(policies, all_pods)
    load_network_policies(
        session=session,
        network_policies=transformed_policies,
        update_tag=update_tag,
        cluster_id=common_job_parameters["CLUSTER_ID"],
        cluster_name=client.name,
    )
    cleanup(session, common_job_parameters)
