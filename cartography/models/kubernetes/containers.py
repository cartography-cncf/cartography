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
class KubernetesContainerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    image: PropertyRef = PropertyRef("image", extra_index=True)
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME", set_in_kwargs=True, extra_index=True
    )
    image_pull_policy: PropertyRef = PropertyRef("image_pull_policy")
    status_image_id: PropertyRef = PropertyRef("status_image_id")
    status_image_sha: PropertyRef = PropertyRef("status_image_sha", extra_index=True)
    status_ready: PropertyRef = PropertyRef("status_ready")
    status_started: PropertyRef = PropertyRef("status_started")
    status_state: PropertyRef = PropertyRef("status_state")
    memory_request: PropertyRef = PropertyRef("memory_request")
    cpu_request: PropertyRef = PropertyRef("cpu_request")
    memory_limit: PropertyRef = PropertyRef("memory_limit")
    cpu_limit: PropertyRef = PropertyRef("cpu_limit")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesContainerToKubernetesNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesContainerToKubernetesPodRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesContainer)<-[:CONTAINS]-(:KubernetesNamespace)
class KubernetesContainerToKubernetesNamespaceRel(CartographyRelSchema):
    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesContainerToKubernetesNamespaceRelProperties = (
        KubernetesContainerToKubernetesNamespaceRelProperties()
    )


@dataclass(frozen=True)
# (:KubernetesContainer)<-[:CONTAINS]-(:KubernetesPod)
class KubernetesContainerToKubernetesPodRel(CartographyRelSchema):
    target_node_label: str = "KubernetesPod"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "namespace": PropertyRef("namespace"),
            "id": PropertyRef("pod_id"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesContainerToKubernetesPodRelProperties = (
        KubernetesContainerToKubernetesPodRelProperties()
    )


@dataclass(frozen=True)
class KubernetesContainerToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesContainer)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesContainerToKubernetesClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesContainerToKubernetesClusterRelProperties = (
        KubernetesContainerToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesContainerToECRImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesContainerToECRImageRel(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("status_image_sha")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: KubernetesContainerToECRImageRelProperties = (
        KubernetesContainerToECRImageRelProperties()
    )


@dataclass(frozen=True)
class KubernetesContainerSchema(CartographyNodeSchema):
    label: str = "KubernetesContainer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Container"])
    properties: KubernetesContainerNodeProperties = KubernetesContainerNodeProperties()
    sub_resource_relationship: KubernetesContainerToKubernetesClusterRel = (
        KubernetesContainerToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesContainerToKubernetesNamespaceRel(),
            KubernetesContainerToKubernetesPodRel(),
            KubernetesContainerToECRImageRel(),
        ]
    )
