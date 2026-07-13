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
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    deletion_timestamp: PropertyRef = PropertyRef("deletion_timestamp")
    pod_selector: PropertyRef = PropertyRef("pod_selector")
    policy_types: PropertyRef = PropertyRef("policy_types")
    ingress_rules: PropertyRef = PropertyRef("ingress_rules")
    egress_rules: PropertyRef = PropertyRef("egress_rules")
    # Derived from policy_types: whether this policy restricts ingress/egress for the
    # pods it selects. A pod selected by a policy with restricts_ingress=True is
    # default-deny for ingress except for what the policy's ingress rules admit.
    # Left unindexed: these booleans are low-selectivity and are read after already
    # scoping to a namespace/pod, so an index would add write cost without helping
    # query plans.
    restricts_ingress: PropertyRef = PropertyRef("restricts_ingress")
    restricts_egress: PropertyRef = PropertyRef("restricts_egress")
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME", set_in_kwargs=True, extra_index=True
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesNetworkPolicyToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesNetworkPolicy)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesNetworkPolicyToKubernetesClusterRel(CartographyRelSchema):
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
