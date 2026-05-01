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
class GCPCloudRunJobContainerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    job_id: PropertyRef = PropertyRef("job_id")
    image: PropertyRef = PropertyRef("image")
    image_digest: PropertyRef = PropertyRef("image_digest")
    architecture: PropertyRef = PropertyRef("architecture")
    architecture_normalized: PropertyRef = PropertyRef("architecture_normalized")
    architecture_source: PropertyRef = PropertyRef("architecture_source")
    project_id: PropertyRef = PropertyRef("project_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToCloudRunJobContainerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToCloudRunJobContainerRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToCloudRunJobContainerRelProperties = (
        ProjectToCloudRunJobContainerRelProperties()
    )


@dataclass(frozen=True)
class CloudRunJobToContainerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: replaced by WORKLOAD_PARENT, will be removed in v1.0.0
@dataclass(frozen=True)
class CloudRunJobToContainerRel(CartographyRelSchema):
    target_node_label: str = "GCPCloudRunJob"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("job_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: CloudRunJobToContainerRelProperties = (
        CloudRunJobToContainerRelProperties()
    )


@dataclass(frozen=True)
class CloudRunJobContainerToJobWorkloadParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPCloudRunJobContainer)-[:WORKLOAD_PARENT]->(:GCPCloudRunJob)
class CloudRunJobContainerToJobWorkloadParentRel(CartographyRelSchema):
    target_node_label: str = "GCPCloudRunJob"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("job_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: CloudRunJobContainerToJobWorkloadParentRelProperties = (
        CloudRunJobContainerToJobWorkloadParentRelProperties()
    )


@dataclass(frozen=True)
class CloudRunJobContainerToECRImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunJobContainerToECRImageRel(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunJobContainerToECRImageRelProperties = (
        CloudRunJobContainerToECRImageRelProperties()
    )


@dataclass(frozen=True)
class CloudRunJobContainerToGitLabContainerImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunJobContainerToGitLabContainerImageRel(CartographyRelSchema):
    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunJobContainerToGitLabContainerImageRelProperties = (
        CloudRunJobContainerToGitLabContainerImageRelProperties()
    )


@dataclass(frozen=True)
class CloudRunJobContainerToArtifactRegistryContainerImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunJobContainerToArtifactRegistryContainerImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunJobContainerToArtifactRegistryContainerImageRelProperties = (
        CloudRunJobContainerToArtifactRegistryContainerImageRelProperties()
    )


@dataclass(frozen=True)
class CloudRunJobContainerToArtifactRegistryPlatformImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunJobContainerToArtifactRegistryPlatformImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryPlatformImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunJobContainerToArtifactRegistryPlatformImageRelProperties = (
        CloudRunJobContainerToArtifactRegistryPlatformImageRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudRunJobContainerSchema(CartographyNodeSchema):
    label: str = "GCPCloudRunJobContainer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Container"])
    properties: GCPCloudRunJobContainerProperties = GCPCloudRunJobContainerProperties()
    sub_resource_relationship: ProjectToCloudRunJobContainerRel = (
        ProjectToCloudRunJobContainerRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudRunJobToContainerRel(),
            CloudRunJobContainerToJobWorkloadParentRel(),
            CloudRunJobContainerToECRImageRel(),
            CloudRunJobContainerToGitLabContainerImageRel(),
            CloudRunJobContainerToArtifactRegistryContainerImageRel(),
            CloudRunJobContainerToArtifactRegistryPlatformImageRel(),
        ],
    )
