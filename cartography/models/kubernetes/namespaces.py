from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class KubernetesNamespaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid", description="UID of the Kubernetes namespace.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the Kubernetes namespace."
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of the creation time of the Kubernetes namespace.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Timestamp of the deletion time of the Kubernetes namespace.",
    )
    status_phase: PropertyRef = PropertyRef(
        "status_phase",
        description="The phase of a Kubernetes namespace indicates whether it is active, terminating, or terminated.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "cluster_name",
        set_in_kwargs=True,
        extra_index=True,
        description="The name of the Kubernetes cluster this namespace belongs to.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class KubernetesNamespaceToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesNamespace)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesNamespaceToKubernetesClusterRel(CartographyRelSchema):
    "Links `KubernetesCluster` to `KubernetesNamespace` with `RESOURCE`."

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesNamespaceToKubernetesClusterRelProperties = (
        KubernetesNamespaceToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesNamespaceToKubernetesClusterWorkloadParentRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesNamespace)-[:WORKLOAD_PARENT]->(:KubernetesCluster)
class KubernetesNamespaceToKubernetesClusterWorkloadParentRel(CartographyRelSchema):
    "Links `KubernetesNamespace` to `KubernetesCluster` with `WORKLOAD_PARENT`."

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: KubernetesNamespaceToKubernetesClusterWorkloadParentRelProperties = (
        KubernetesNamespaceToKubernetesClusterWorkloadParentRelProperties()
    )


@dataclass(frozen=True)
class KubernetesNamespaceSchema(CartographyNodeSchema):
    "A namespace that scopes resources in a Kubernetes cluster."

    label: str = "KubernetesNamespace"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeNamespace"])
    properties: KubernetesNamespaceNodeProperties = KubernetesNamespaceNodeProperties()
    sub_resource_relationship: KubernetesNamespaceToKubernetesClusterRel = (
        KubernetesNamespaceToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesNamespaceToKubernetesClusterWorkloadParentRel(),
        ]
    )
