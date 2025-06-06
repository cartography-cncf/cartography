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
class KubernetesContainerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    image: PropertyRef = PropertyRef("image", extra_index=True)
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME", set_in_kwargs=True, extra_index=True
    )
    pod_name: PropertyRef = PropertyRef("pod_name", extra_index=True)
    image_pull_policy: PropertyRef = PropertyRef("image_pull_policy")
    status_image_id: PropertyRef = PropertyRef("status_image_id")
    status_image_sha: PropertyRef = PropertyRef("status_image_sha")
    status_ready: PropertyRef = PropertyRef("status_ready")
    status_started: PropertyRef = PropertyRef("status_started")
    status_state: PropertyRef = PropertyRef("status_state")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesContainerToKubernetesNamespaceProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesContainerToKubernetesPodProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesContainer)<-[:CONTAINS]-(:KubernetesNamespace)
class KubernetesContainerToKubernetesNamespace(CartographyRelSchema):
    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesContainerToKubernetesNamespaceProperties = (
        KubernetesContainerToKubernetesNamespaceProperties()
    )


@dataclass(frozen=True)
# (:KubernetesContainer)<-[:CONTAINS]-(:KubernetesPod)
class KubernetesContainerToKubernetesPod(CartographyRelSchema):
    target_node_label: str = "KubernetesPod"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "namespace": PropertyRef("namespace"),
            "name": PropertyRef("pod_name"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesContainerToKubernetesPodProperties = (
        KubernetesContainerToKubernetesPodProperties()
    )


@dataclass(frozen=True)
class KubernetesContainerToKubernetesClusterProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesContainer)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesContainerToKubernetesCluster(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesContainerToKubernetesClusterProperties = (
        KubernetesContainerToKubernetesClusterProperties()
    )


@dataclass(frozen=True)
class KubernetesContainerSchema(CartographyNodeSchema):
    label: str = "KubernetesContainer"
    properties: KubernetesContainerNodeProperties = KubernetesContainerNodeProperties()
    sub_resource_relationship: KubernetesContainerToKubernetesCluster = (
        KubernetesContainerToKubernetesCluster()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesContainerToKubernetesNamespace(),
            KubernetesContainerToKubernetesPod(),
        ]
    )
