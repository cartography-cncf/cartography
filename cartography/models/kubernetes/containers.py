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
    image_pull_policy: PropertyRef = PropertyRef("image_pull_policy")
    status_image_id: PropertyRef = PropertyRef("status_image_id")
    status_image_sha: PropertyRef = PropertyRef("status_image_sha", extra_index=True)  # Used in digest joins (21 times)
    resolved_image_digest: PropertyRef = PropertyRef("resolvedImageDigest")  # NEW: Resolved platform-specific image (if status_image_sha is manifest_list)
    manifest_list_digest: PropertyRef = PropertyRef("manifestListDigest")  # NEW: Original manifest list digest (null if direct image)
    status_ready: PropertyRef = PropertyRef("status_ready")
    status_started: PropertyRef = PropertyRef("status_started")
    status_state: PropertyRef = PropertyRef("status_state", extra_index=True)  # Filtered 21 times (WHERE status_state = 'running')
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
class KubernetesContainerToResolvedImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesContainerToResolvedImageRel(CartographyRelSchema):
    """
    NEW: Points to the actual platform-specific image (type='image').
    If status_image_sha is a manifest_list, this is resolved at ingest time
    by following CONTAINS_IMAGE and matching architecture.
    """
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("resolvedImageDigest")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_RESOLVED_IMAGE"
    properties: KubernetesContainerToResolvedImageRelProperties = (
        KubernetesContainerToResolvedImageRelProperties()
    )


@dataclass(frozen=True)
class KubernetesContainerToManifestListRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesContainerToManifestListRel(CartographyRelSchema):
    """
    NEW: Points to manifest_list if the container uses a multi-arch image.
    Null/not present if container uses a direct platform-specific image.
    """
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("manifestListDigest")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_MANIFEST_LIST"
    properties: KubernetesContainerToManifestListRelProperties = (
        KubernetesContainerToManifestListRelProperties()
    )


@dataclass(frozen=True)
class KubernetesContainerSchema(CartographyNodeSchema):
    label: str = "KubernetesContainer"
    properties: KubernetesContainerNodeProperties = KubernetesContainerNodeProperties()
    sub_resource_relationship: KubernetesContainerToKubernetesClusterRel = (
        KubernetesContainerToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesContainerToKubernetesNamespaceRel(),
            KubernetesContainerToKubernetesPodRel(),
            KubernetesContainerToResolvedImageRel(),  # NEW: Always points to type='image'
            KubernetesContainerToManifestListRel(),  # NEW: Points to manifest_list if applicable
        ]
    )
