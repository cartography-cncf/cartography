from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class KubernetesNetworkPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid", description="UID of the network policy.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the network policy."
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="The Kubernetes namespace where this network policy is defined.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of the creation time of the network policy.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Timestamp of the deletion time of the network policy.",
    )
    pod_selector: PropertyRef = PropertyRef(
        "pod_selector",
        description="The `spec.podSelector` selecting the pods this policy applies to, stored as a JSON-encoded `{match_labels, match_expressions}`. An empty selector selects every pod in the namespace.",
    )
    policy_types: PropertyRef = PropertyRef(
        "policy_types",
        description="List of policy types the policy governs, e.g. `['Ingress']`, `['Ingress', 'Egress']`.",
    )
    ingress_rules: PropertyRef = PropertyRef(
        "ingress_rules",
        description="The `spec.ingress` rule set (from-peers and ports), stored as a JSON-encoded string.",
    )
    egress_rules: PropertyRef = PropertyRef(
        "egress_rules",
        description="The `spec.egress` rule set (to-peers and ports), stored as a JSON-encoded string.",
    )
    # Derived from policy_types: whether this policy restricts ingress/egress for the
    # pods it selects. A pod selected by a policy with restricts_ingress=True is
    # default-deny for ingress except for what the policy's ingress rules admit.
    # Left unindexed: these booleans are low-selectivity and are read after already
    # scoping to a namespace/pod, so an index would add write cost without helping
    # query plans.
    restricts_ingress: PropertyRef = PropertyRef(
        "restricts_ingress",
        description="`true` when `Ingress` is in `policy_types`: the selected pods are default-deny for ingress except for what `ingress_rules` admit.",
    )
    restricts_egress: PropertyRef = PropertyRef(
        "restricts_egress",
        description="`true` when `Egress` is in `policy_types`: the selected pods are default-deny for egress except for what `egress_rules` admit.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster where this network policy is defined.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class KubernetesNetworkPolicyToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesNetworkPolicy)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesNetworkPolicyToKubernetesClusterRel(CartographyRelSchema):
    "Links `KubernetesCluster` to `KubernetesNetworkPolicy` with `RESOURCE`."

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesNetworkPolicyToKubernetesClusterRelProperties = (
        KubernetesNetworkPolicyToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesNetworkPolicyToKubernetesNamespaceRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesNetworkPolicy)<-[:CONTAINS]-(:KubernetesNamespace)
class KubernetesNetworkPolicyToKubernetesNamespaceRel(CartographyRelSchema):
    "Links `KubernetesNamespace` to `KubernetesNetworkPolicy` with `CONTAINS`."

    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesNetworkPolicyToKubernetesNamespaceRelProperties = (
        KubernetesNetworkPolicyToKubernetesNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesNetworkPolicyToKubernetesPodRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesNetworkPolicy)-[:APPLIES_TO]->(:KubernetesPod)
# The policy's resolved podSelector: the pods it governs. An empty selector
# selects every pod in the namespace.
class KubernetesNetworkPolicyToKubernetesPodRel(CartographyRelSchema):
    "Links `KubernetesNetworkPolicy` to `KubernetesPod` with `APPLIES_TO`."

    target_node_label: str = "KubernetesPod"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "namespace": PropertyRef("namespace"),
            "id": PropertyRef("pod_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: KubernetesNetworkPolicyToKubernetesPodRelProperties = (
        KubernetesNetworkPolicyToKubernetesPodRelProperties()
    )


@dataclass(frozen=True)
class KubernetesNetworkPolicySchema(CartographyNodeSchema):
    "A Kubernetes network policy that controls pod traffic."

    label: str = "KubernetesNetworkPolicy"
    properties: KubernetesNetworkPolicyNodeProperties = (
        KubernetesNetworkPolicyNodeProperties()
    )
    sub_resource_relationship: KubernetesNetworkPolicyToKubernetesClusterRel = (
        KubernetesNetworkPolicyToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesNetworkPolicyToKubernetesNamespaceRel(),
            KubernetesNetworkPolicyToKubernetesPodRel(),
        ]
    )
