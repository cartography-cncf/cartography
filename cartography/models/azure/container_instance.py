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
from cartography.models.ontology.labels import CONTAINER


@dataclass(frozen=True)
class AzureContainerInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Identifier derived from the container group and container name.",
    )
    name: PropertyRef = PropertyRef("name", description="Name of the container.")
    group_id: PropertyRef = PropertyRef(
        "group_id",
        description="Full Azure resource ID of the containing container group.",
    )
    image: PropertyRef = PropertyRef(
        "image", description="Container image reference configured for the container."
    )
    image_digest: PropertyRef = PropertyRef(
        "image_digest", description="Digest parsed from the container image reference."
    )
    architecture: PropertyRef = PropertyRef(
        "architecture",
        description="Container host architecture used by Azure Container Instances.",
    )
    architecture_normalized: PropertyRef = PropertyRef(
        "architecture_normalized",
        description="Normalized container host architecture.",
    )
    state: PropertyRef = PropertyRef(
        "state", description="Current runtime state of the container."
    )
    cpu_request: PropertyRef = PropertyRef(
        "cpu_request", description="Requested CPU cores for the container."
    )
    memory_request_gb: PropertyRef = PropertyRef(
        "memory_request_gb", description="Requested memory in gigabytes."
    )
    cpu_limit: PropertyRef = PropertyRef(
        "cpu_limit", description="Maximum CPU cores available to the container."
    )
    memory_limit_gb: PropertyRef = PropertyRef(
        "memory_limit_gb", description="Maximum memory available in gigabytes."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerInstanceToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerInstanceToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the container as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureContainerInstanceToSubscriptionRelProperties = (
        AzureContainerInstanceToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureGroupContainerToContainerInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: replaced by WORKLOAD_PARENT, will be removed in v1.0.0
@dataclass(frozen=True)
class AzureGroupContainerToContainerInstanceRel(CartographyRelSchema):
    """Deprecated compatibility edge from a container group to its container."""

    target_node_label: str = "AzureGroupContainer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureGroupContainerToContainerInstanceRelProperties = (
        AzureGroupContainerToContainerInstanceRelProperties()
    )


@dataclass(frozen=True)
class AzureContainerInstanceToGroupContainerWorkloadParentRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureContainerInstance)-[:WORKLOAD_PARENT]->(:AzureGroupContainer)
class AzureContainerInstanceToGroupContainerWorkloadParentRel(CartographyRelSchema):
    """A container runs within an Azure container group."""

    target_node_label: str = "AzureGroupContainer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: AzureContainerInstanceToGroupContainerWorkloadParentRelProperties = (
        AzureContainerInstanceToGroupContainerWorkloadParentRelProperties()
    )


@dataclass(frozen=True)
class AzureContainerInstanceToECRImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerInstanceToECRImageRel(CartographyRelSchema):
    """An Azure container uses an Amazon ECR image with the same digest."""

    target_node_label: str = "AWSECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: AzureContainerInstanceToECRImageRelProperties = (
        AzureContainerInstanceToECRImageRelProperties()
    )


@dataclass(frozen=True)
class AzureContainerInstanceToGitLabContainerImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerInstanceToGitLabContainerImageRel(CartographyRelSchema):
    """An Azure container uses a GitLab container image with the same digest."""

    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: AzureContainerInstanceToGitLabContainerImageRelProperties = (
        AzureContainerInstanceToGitLabContainerImageRelProperties()
    )


@dataclass(frozen=True)
class AzureContainerInstanceToGCPArtifactRegistryImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerInstanceToGCPArtifactRegistryImageRel(CartographyRelSchema):
    """An Azure container uses a Google Artifact Registry image with the same digest."""

    target_node_label: str = "GCPArtifactRegistryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: AzureContainerInstanceToGCPArtifactRegistryImageRelProperties = (
        AzureContainerInstanceToGCPArtifactRegistryImageRelProperties()
    )


@dataclass(frozen=True)
class AzureContainerInstanceToGitHubContainerImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerInstanceToGitHubContainerImageRel(CartographyRelSchema):
    """An Azure container uses a GitHub container image with the same digest."""

    target_node_label: str = "GitHubContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: AzureContainerInstanceToGitHubContainerImageRelProperties = (
        AzureContainerInstanceToGitHubContainerImageRelProperties()
    )


@dataclass(frozen=True)
class AzureContainerInstanceSchema(CartographyNodeSchema):
    """An individual container running in an Azure container group."""

    label: str = "AzureContainerInstance"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CONTAINER])
    properties: AzureContainerInstanceNodeProperties = (
        AzureContainerInstanceNodeProperties()
    )
    sub_resource_relationship: AzureContainerInstanceToSubscriptionRel = (
        AzureContainerInstanceToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureGroupContainerToContainerInstanceRel(),
            AzureContainerInstanceToGroupContainerWorkloadParentRel(),
            AzureContainerInstanceToECRImageRel(),
            AzureContainerInstanceToGitLabContainerImageRel(),
            AzureContainerInstanceToGCPArtifactRegistryImageRel(),
            AzureContainerInstanceToGitHubContainerImageRel(),
        ],
    )
