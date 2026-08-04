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
from cartography.models.ontology.labels import COMPUTE_SERVICE


@dataclass(frozen=True)
class KubernetesDaemonSetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid", description="UID of the Kubernetes DaemonSet.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the Kubernetes DaemonSet."
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="Kubernetes namespace containing the DaemonSet.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp when the Kubernetes DaemonSet was created.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Timestamp when the Kubernetes DaemonSet was marked for deletion.",
    )
    desired_number_scheduled: PropertyRef = PropertyRef(
        "desired_number_scheduled",
        description="Number of nodes that should run a pod from the DaemonSet.",
    )
    number_ready: PropertyRef = PropertyRef(
        "number_ready",
        description="Number of nodes running a ready pod from the DaemonSet.",
    )
    labels: PropertyRef = PropertyRef(
        "labels",
        description="Metadata labels on the DaemonSet, stored as a JSON-encoded string.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster containing the DaemonSet.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesDaemonSetToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesDaemonSet)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesDaemonSetToKubernetesClusterRel(CartographyRelSchema):
    """Links a cluster to one of its daemon sets."""

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesDaemonSetToKubernetesClusterRelProperties = (
        KubernetesDaemonSetToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesDaemonSetToKubernetesNamespaceWorkloadParentRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesDaemonSet)-[:WORKLOAD_PARENT]->(:KubernetesNamespace)
class KubernetesDaemonSetToKubernetesNamespaceWorkloadParentRel(CartographyRelSchema):
    """Links a daemon set to the namespace that owns it."""

    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: KubernetesDaemonSetToKubernetesNamespaceWorkloadParentRelProperties = (
        KubernetesDaemonSetToKubernetesNamespaceWorkloadParentRelProperties()
    )


@dataclass(frozen=True)
class KubernetesDaemonSetSchema(CartographyNodeSchema):
    "A Kubernetes DaemonSet that runs pods across selected cluster nodes."

    label: str = "KubernetesDaemonSet"
    # ComputeService is the cross-provider "logical workload / controller" label.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_SERVICE])
    properties: KubernetesDaemonSetNodeProperties = KubernetesDaemonSetNodeProperties()
    sub_resource_relationship: KubernetesDaemonSetToKubernetesClusterRel = (
        KubernetesDaemonSetToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesDaemonSetToKubernetesNamespaceWorkloadParentRel(),
        ]
    )
