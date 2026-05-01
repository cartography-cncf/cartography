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
class GCPCloudRunServiceContainerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    service_id: PropertyRef = PropertyRef("service_id")
    image: PropertyRef = PropertyRef("image")
    image_digest: PropertyRef = PropertyRef("image_digest")
    architecture: PropertyRef = PropertyRef("architecture")
    architecture_normalized: PropertyRef = PropertyRef("architecture_normalized")
    architecture_source: PropertyRef = PropertyRef("architecture_source")
    project_id: PropertyRef = PropertyRef("project_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToCloudRunServiceContainerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToCloudRunServiceContainerRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToCloudRunServiceContainerRelProperties = (
        ProjectToCloudRunServiceContainerRelProperties()
    )


@dataclass(frozen=True)
class CloudRunServiceToContainerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: replaced by WORKLOAD_PARENT, will be removed in v1.0.0
@dataclass(frozen=True)
class CloudRunServiceToContainerRel(CartographyRelSchema):
    target_node_label: str = "GCPCloudRunService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: CloudRunServiceToContainerRelProperties = (
        CloudRunServiceToContainerRelProperties()
    )


@dataclass(frozen=True)
class CloudRunServiceContainerToServiceWorkloadParentRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPCloudRunServiceContainer)-[:WORKLOAD_PARENT]->(:GCPCloudRunService)
class CloudRunServiceContainerToServiceWorkloadParentRel(CartographyRelSchema):
    target_node_label: str = "GCPCloudRunService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: CloudRunServiceContainerToServiceWorkloadParentRelProperties = (
        CloudRunServiceContainerToServiceWorkloadParentRelProperties()
    )


@dataclass(frozen=True)
class CloudRunServiceContainerToECRImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunServiceContainerToECRImageRel(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunServiceContainerToECRImageRelProperties = (
        CloudRunServiceContainerToECRImageRelProperties()
    )


@dataclass(frozen=True)
class CloudRunServiceContainerToGitLabContainerImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunServiceContainerToGitLabContainerImageRel(CartographyRelSchema):
    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunServiceContainerToGitLabContainerImageRelProperties = (
        CloudRunServiceContainerToGitLabContainerImageRelProperties()
    )


@dataclass(frozen=True)
class CloudRunServiceContainerToArtifactRegistryContainerImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunServiceContainerToArtifactRegistryContainerImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: (
        CloudRunServiceContainerToArtifactRegistryContainerImageRelProperties
    ) = CloudRunServiceContainerToArtifactRegistryContainerImageRelProperties()


@dataclass(frozen=True)
class CloudRunServiceContainerToArtifactRegistryPlatformImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunServiceContainerToArtifactRegistryPlatformImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryPlatformImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunServiceContainerToArtifactRegistryPlatformImageRelProperties = (
        CloudRunServiceContainerToArtifactRegistryPlatformImageRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudRunServiceContainerSchema(CartographyNodeSchema):
    label: str = "GCPCloudRunServiceContainer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Container"])
    properties: GCPCloudRunServiceContainerProperties = (
        GCPCloudRunServiceContainerProperties()
    )
    sub_resource_relationship: ProjectToCloudRunServiceContainerRel = (
        ProjectToCloudRunServiceContainerRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudRunServiceToContainerRel(),
            CloudRunServiceContainerToServiceWorkloadParentRel(),
            CloudRunServiceContainerToECRImageRel(),
            CloudRunServiceContainerToGitLabContainerImageRel(),
            CloudRunServiceContainerToArtifactRegistryContainerImageRel(),
            CloudRunServiceContainerToArtifactRegistryPlatformImageRel(),
        ],
    )
