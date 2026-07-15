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
    id: PropertyRef = PropertyRef(
        "id", description="Stable identifier for this resource."
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Name of the container as declared in the task template. Falls back to the container index when the Cloud Run API omits the field (single-container jobs).",
    )
    job_id: PropertyRef = PropertyRef(
        "job_id", description="Full resource name of the parent GCPCloudRunJob."
    )
    image: PropertyRef = PropertyRef(
        "image",
        description="The container image reference as declared in the task template.",
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
class ProjectToCloudRunJobContainerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class CloudRunJobContainerToECRImageRel(CartographyRelSchema):
    target_node_label: str = "AWSECRImage"
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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
class CloudRunJobContainerToArtifactRegistryImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class CloudRunJobContainerToArtifactRegistryImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunJobContainerToArtifactRegistryImageRelProperties = (
        CloudRunJobContainerToArtifactRegistryImageRelProperties()
    )


@dataclass(frozen=True)
class CloudRunJobContainerToGitHubContainerImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class CloudRunJobContainerToGitHubContainerImageRel(CartographyRelSchema):
    target_node_label: str = "GitHubContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: CloudRunJobContainerToGitHubContainerImageRelProperties = (
        CloudRunJobContainerToGitHubContainerImageRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudRunJobContainerSchema(CartographyNodeSchema):
    """A Google Cloud Cloud Run Job Container resource."""

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
            CloudRunJobContainerToArtifactRegistryImageRel(),
            CloudRunJobContainerToGitHubContainerImageRel(),
        ],
    )
