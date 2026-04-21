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
class GCPCloudRunContainerProperties(CartographyNodeProperties):
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
class ProjectToCloudRunContainerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToCloudRunContainerRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToCloudRunContainerRelProperties = (
        ProjectToCloudRunContainerRelProperties()
    )


@dataclass(frozen=True)
class CloudRunJobToContainerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
class CloudRunContainerToECRImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunContainerToECRImageRel(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunContainerToECRImageRelProperties = (
        CloudRunContainerToECRImageRelProperties()
    )


@dataclass(frozen=True)
class CloudRunContainerToGitLabContainerImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunContainerToGitLabContainerImageRel(CartographyRelSchema):
    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunContainerToGitLabContainerImageRelProperties = (
        CloudRunContainerToGitLabContainerImageRelProperties()
    )


@dataclass(frozen=True)
class CloudRunContainerToArtifactRegistryContainerImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunContainerToArtifactRegistryContainerImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunContainerToArtifactRegistryContainerImageRelProperties = (
        CloudRunContainerToArtifactRegistryContainerImageRelProperties()
    )


@dataclass(frozen=True)
class CloudRunContainerToArtifactRegistryPlatformImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunContainerToArtifactRegistryPlatformImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryPlatformImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunContainerToArtifactRegistryPlatformImageRelProperties = (
        CloudRunContainerToArtifactRegistryPlatformImageRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudRunContainerSchema(CartographyNodeSchema):
    label: str = "GCPCloudRunContainer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Container"])
    properties: GCPCloudRunContainerProperties = GCPCloudRunContainerProperties()
    sub_resource_relationship: ProjectToCloudRunContainerRel = (
        ProjectToCloudRunContainerRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudRunJobToContainerRel(),
            CloudRunContainerToECRImageRel(),
            CloudRunContainerToGitLabContainerImageRel(),
            CloudRunContainerToArtifactRegistryContainerImageRel(),
            CloudRunContainerToArtifactRegistryPlatformImageRel(),
        ],
    )
