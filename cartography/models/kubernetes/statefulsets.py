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
class KubernetesStatefulSetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    deletion_timestamp: PropertyRef = PropertyRef("deletion_timestamp")
    replicas: PropertyRef = PropertyRef("replicas")
    ready_replicas: PropertyRef = PropertyRef("ready_replicas")
    service_name: PropertyRef = PropertyRef("service_name")
    labels: PropertyRef = PropertyRef("labels")
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME", set_in_kwargs=True, extra_index=True
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesStatefulSetToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesStatefulSet)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesStatefulSetToKubernetesClusterRel(CartographyRelSchema):
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
    label: str = "KubernetesStatefulSet"
    # ComputeService is the cross-provider "logical workload / controller" label.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeService"])
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
