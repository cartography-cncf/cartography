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
class KubernetesStatefulSetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "uid", description="UID of the Kubernetes StatefulSet."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the Kubernetes StatefulSet."
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        extra_index=True,
        description="Kubernetes namespace containing the StatefulSet.",
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp when the Kubernetes StatefulSet was created.",
    )
    deletion_timestamp: PropertyRef = PropertyRef(
        "deletion_timestamp",
        description="Timestamp when the Kubernetes StatefulSet was marked for deletion.",
    )
    replicas: PropertyRef = PropertyRef(
        "replicas", description="Desired number of pod replicas."
    )
    ready_replicas: PropertyRef = PropertyRef(
        "ready_replicas", description="Number of pod replicas that are ready."
    )
    service_name: PropertyRef = PropertyRef(
        "service_name",
        description="Name of the governing Kubernetes Service.",
    )
    labels: PropertyRef = PropertyRef(
        "labels",
        description="Metadata labels on the StatefulSet, stored as a JSON-encoded string.",
    )
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME",
        set_in_kwargs=True,
        extra_index=True,
        description="Name of the Kubernetes cluster containing the StatefulSet.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesStatefulSetToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesStatefulSet)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesStatefulSetToKubernetesClusterRel(CartographyRelSchema):
    """Links a cluster to one of its stateful sets."""

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesStatefulSetToKubernetesClusterRelProperties = (
        KubernetesStatefulSetToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesStatefulSetToKubernetesNamespaceWorkloadParentRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesStatefulSet)-[:WORKLOAD_PARENT]->(:KubernetesNamespace)
class KubernetesStatefulSetToKubernetesNamespaceWorkloadParentRel(CartographyRelSchema):
    """Links a stateful set to the namespace that owns it."""

    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: (
        KubernetesStatefulSetToKubernetesNamespaceWorkloadParentRelProperties
    ) = KubernetesStatefulSetToKubernetesNamespaceWorkloadParentRelProperties()


@dataclass(frozen=True)
class KubernetesStatefulSetSchema(CartographyNodeSchema):
    "A Kubernetes StatefulSet that manages pods with stable identities."

    label: str = "KubernetesStatefulSet"
    # ComputeService is the cross-provider "logical workload / controller" label.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_SERVICE])
    properties: KubernetesStatefulSetNodeProperties = (
        KubernetesStatefulSetNodeProperties()
    )
    sub_resource_relationship: KubernetesStatefulSetToKubernetesClusterRel = (
        KubernetesStatefulSetToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesStatefulSetToKubernetesNamespaceWorkloadParentRel(),
        ]
    )
