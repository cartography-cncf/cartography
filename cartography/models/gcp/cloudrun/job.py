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
class GCPCloudRunJobProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    container_image: PropertyRef = PropertyRef("container_image")
    image_digest: PropertyRef = PropertyRef("image_digest")
    architecture: PropertyRef = PropertyRef("architecture")
    architecture_normalized: PropertyRef = PropertyRef("architecture_normalized")
    architecture_source: PropertyRef = PropertyRef("architecture_source")
    service_account_email: PropertyRef = PropertyRef("service_account_email")
    project_id: PropertyRef = PropertyRef("project_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToCloudRunJobRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToCloudRunJobRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToCloudRunJobRelProperties = ProjectToCloudRunJobRelProperties()


@dataclass(frozen=True)
class CloudRunJobToServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunJobToServiceAccountRel(CartographyRelSchema):
    target_node_label: str = "GCPServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("service_account_email")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SERVICE_ACCOUNT"
    properties: CloudRunJobToServiceAccountRelProperties = (
        CloudRunJobToServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudRunJobToECRImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunJobToECRImageRel(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunJobToECRImageRelProperties = (
        CloudRunJobToECRImageRelProperties()
    )


@dataclass(frozen=True)
class CloudRunJobToGitLabContainerImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunJobToGitLabContainerImageRel(CartographyRelSchema):
    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunJobToGitLabContainerImageRelProperties = (
        CloudRunJobToGitLabContainerImageRelProperties()
    )


@dataclass(frozen=True)
class CloudRunJobToGCPArtifactRegistryContainerImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudRunJobToGCPArtifactRegistryContainerImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunJobToGCPArtifactRegistryContainerImageRelProperties = (
        CloudRunJobToGCPArtifactRegistryContainerImageRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudRunJobSchema(CartographyNodeSchema):
    label: str = "GCPCloudRunJob"
    properties: GCPCloudRunJobProperties = GCPCloudRunJobProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Function"])
    sub_resource_relationship: ProjectToCloudRunJobRel = ProjectToCloudRunJobRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudRunJobToServiceAccountRel(),
            CloudRunJobToECRImageRel(),
            CloudRunJobToGitLabContainerImageRel(),
            CloudRunJobToGCPArtifactRegistryContainerImageRel(),
        ],
    )
