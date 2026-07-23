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
class KubernetesCronJobNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    deletion_timestamp: PropertyRef = PropertyRef("deletion_timestamp")
    schedule: PropertyRef = PropertyRef("schedule")
    suspend: PropertyRef = PropertyRef("suspend")
    labels: PropertyRef = PropertyRef("labels")
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME", set_in_kwargs=True, extra_index=True
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesCronJobToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesCronJob)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesCronJobToKubernetesClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesCronJobToKubernetesClusterRelProperties = (
        KubernetesCronJobToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesCronJobToKubernetesNamespaceWorkloadParentRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesCronJob)-[:WORKLOAD_PARENT]->(:KubernetesNamespace)
class KubernetesCronJobToKubernetesNamespaceWorkloadParentRel(CartographyRelSchema):
    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: KubernetesCronJobToKubernetesNamespaceWorkloadParentRelProperties = (
        KubernetesCronJobToKubernetesNamespaceWorkloadParentRelProperties()
    )


@dataclass(frozen=True)
class KubernetesCronJobSchema(CartographyNodeSchema):
    label: str = "KubernetesCronJob"
    # ComputeService is the cross-provider "logical workload / controller" label.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeService"])
    properties: KubernetesCronJobNodeProperties = KubernetesCronJobNodeProperties()
    sub_resource_relationship: KubernetesCronJobToKubernetesClusterRel = (
        KubernetesCronJobToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesCronJobToKubernetesNamespaceWorkloadParentRel(),
        ]
    )
