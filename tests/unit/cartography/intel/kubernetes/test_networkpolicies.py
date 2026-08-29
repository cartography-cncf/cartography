import json

from kubernetes.client.models import V1IPBlock
from kubernetes.client.models import V1LabelSelector
from kubernetes.client.models import V1NetworkPolicy
from kubernetes.client.models import V1NetworkPolicyEgressRule
from kubernetes.client.models import V1NetworkPolicyIngressRule
from kubernetes.client.models import V1NetworkPolicyPeer
from kubernetes.client.models import V1NetworkPolicyPort
from kubernetes.client.models import V1NetworkPolicySpec
from kubernetes.client.models import V1ObjectMeta

from cartography.intel.kubernetes.networkpolicies import transform_network_policies

ALL_PODS = [
    {"uid": "pod-a", "namespace": "app", "labels": json.dumps({"role": "web"})},
    {"uid": "pod-b", "namespace": "app", "labels": json.dumps({"role": "db"})},
    {"uid": "pod-c", "namespace": "other", "labels": json.dumps({"role": "web"})},
]


def _policy(name, namespace, spec):
    return V1NetworkPolicy(
        metadata=V1ObjectMeta(
            uid=name,
            name=name,
            namespace=namespace,
            creation_timestamp=None,
            deletion_timestamp=None,
        ),
        spec=spec,
    )


def test_empty_selector_selects_all_pods_in_namespace():
    policy = _policy(
        "default-deny",
        "app",
        V1NetworkPolicySpec(
            pod_selector=V1LabelSelector(),
            policy_types=["Ingress"],
        ),
    )

    [transformed] = transform_network_policies([policy], ALL_PODS)

    # Empty selector => every pod in the same namespace, but not other namespaces.
    assert sorted(transformed["pod_ids"]) == ["pod-a", "pod-b"]
    assert transformed["restricts_ingress"] is True
    assert transformed["restricts_egress"] is False


def test_label_selector_scopes_to_matching_pods():
    policy = _policy(
        "web-only",
        "app",
        V1NetworkPolicySpec(
            pod_selector=V1LabelSelector(match_labels={"role": "web"}),
            policy_types=["Ingress"],
            ingress=[
                V1NetworkPolicyIngressRule(
                    _from=[
                        V1NetworkPolicyPeer(
                            ip_block=V1IPBlock(
                                cidr="10.0.0.0/8", _except=["10.1.0.0/16"]
                            )
                        )
                    ],
                    ports=[V1NetworkPolicyPort(port=8080, protocol="TCP")],
                )
            ],
        ),
    )

    [transformed] = transform_network_policies([policy], ALL_PODS)

    assert transformed["pod_ids"] == ["pod-a"]
    # Raw ingress rules are retained as JSON, including the ipBlock peer + ports.
    ingress = json.loads(transformed["ingress_rules"])
    assert ingress[0]["from"][0]["ip_block"] == {
        "cidr": "10.0.0.0/8",
        "except": ["10.1.0.0/16"],
    }
    assert ingress[0]["ports"] == [{"port": 8080, "protocol": "TCP", "end_port": None}]


def test_egress_policy_sets_restricts_egress():
    policy = _policy(
        "egress-only",
        "app",
        V1NetworkPolicySpec(
            pod_selector=V1LabelSelector(match_labels={"role": "db"}),
            policy_types=["Egress"],
            egress=[
                V1NetworkPolicyEgressRule(
                    to=[
                        V1NetworkPolicyPeer(
                            namespace_selector=V1LabelSelector(
                                match_labels={"team": "data"}
                            )
                        )
                    ],
                )
            ],
        ),
    )

    [transformed] = transform_network_policies([policy], ALL_PODS)

    assert transformed["pod_ids"] == ["pod-b"]
    assert transformed["restricts_ingress"] is False
    assert transformed["restricts_egress"] is True
    egress = json.loads(transformed["egress_rules"])
    assert egress[0]["to"][0]["namespace_selector"] == {
        "match_labels": {"team": "data"},
        "match_expressions": None,
    }
