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
    id: PropertyRef = PropertyRef(
        "id", description="Stable identifier for this resource."
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Name of the container as declared in the spec. Falls back to the container index when the Cloud Run API omits the field (single-container deployments).",
    )
    service_id: PropertyRef = PropertyRef(
        "service_id", description="Full resource name of the parent GCPCloudRunService."
    )
    image: PropertyRef = PropertyRef(
        "image", description="The container image reference as declared in the spec."
    )
    image_digest: PropertyRef = PropertyRef(
        "image_digest",
        description="The digest portion of the image reference (e.g., `sha256:abc...`) when the image is pinned by digest; `None` for tag-based references.",
    )
    architecture: PropertyRef = PropertyRef(
        "architecture",
        description="CPU architecture (always `amd64`; Cloud Run does not support ARM).",
    )
    architecture_normalized: PropertyRef = PropertyRef(
        "architecture_normalized",
        description="Normalized architecture value (always `amd64`).",
    )
    architecture_source: PropertyRef = PropertyRef(
        "architecture_source",
        description="How the architecture was determined (always `platform_requirement`).",
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="The GCP project ID this container belongs to."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class ProjectToCloudRunServiceContainerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class CloudRunServiceContainerToECRImageRel(CartographyRelSchema):
    target_node_label: str = "AWSECRImage"
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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
class CloudRunServiceContainerToArtifactRegistryImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class CloudRunServiceContainerToArtifactRegistryImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunServiceContainerToArtifactRegistryImageRelProperties = (
        CloudRunServiceContainerToArtifactRegistryImageRelProperties()
    )


@dataclass(frozen=True)
class CloudRunServiceContainerToGitHubContainerImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class CloudRunServiceContainerToGitHubContainerImageRel(CartographyRelSchema):
    target_node_label: str = "GitHubContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunServiceContainerToGitHubContainerImageRelProperties = (
        CloudRunServiceContainerToGitHubContainerImageRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudRunServiceContainerSchema(CartographyNodeSchema):
    """A Google Cloud Cloud Run Service Container resource."""

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
            CloudRunServiceContainerToArtifactRegistryImageRel(),
            CloudRunServiceContainerToGitHubContainerImageRel(),
        ],
    )
