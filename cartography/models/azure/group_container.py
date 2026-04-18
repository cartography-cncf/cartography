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
class AzureGroupContainerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    group_id: PropertyRef = PropertyRef("group_id")
    image: PropertyRef = PropertyRef("image")
    image_digest: PropertyRef = PropertyRef("image_digest")
    architecture: PropertyRef = PropertyRef("architecture")
    architecture_normalized: PropertyRef = PropertyRef("architecture_normalized")
    cpu_request: PropertyRef = PropertyRef("cpu_request")
    memory_request_gb: PropertyRef = PropertyRef("memory_request_gb")
    cpu_limit: PropertyRef = PropertyRef("cpu_limit")
    memory_limit_gb: PropertyRef = PropertyRef("memory_limit_gb")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureGroupContainerToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureGroupContainerToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureGroupContainerToSubscriptionRelProperties = (
        AzureGroupContainerToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureContainerInstanceToGroupContainerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerInstanceToGroupContainerRel(CartographyRelSchema):
    target_node_label: str = "AzureContainerInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureContainerInstanceToGroupContainerRelProperties = (
        AzureContainerInstanceToGroupContainerRelProperties()
    )


@dataclass(frozen=True)
class AzureGroupContainerToECRImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureGroupContainerToECRImageRel(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: AzureGroupContainerToECRImageRelProperties = (
        AzureGroupContainerToECRImageRelProperties()
    )


@dataclass(frozen=True)
class AzureGroupContainerToGitLabContainerImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureGroupContainerToGitLabContainerImageRel(CartographyRelSchema):
    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: AzureGroupContainerToGitLabContainerImageRelProperties = (
        AzureGroupContainerToGitLabContainerImageRelProperties()
    )


@dataclass(frozen=True)
class AzureGroupContainerToGCPArtifactRegistryContainerImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureGroupContainerToGCPArtifactRegistryContainerImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: AzureGroupContainerToGCPArtifactRegistryContainerImageRelProperties = (
        AzureGroupContainerToGCPArtifactRegistryContainerImageRelProperties()
    )


@dataclass(frozen=True)
class AzureGroupContainerToGCPArtifactRegistryPlatformImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureGroupContainerToGCPArtifactRegistryPlatformImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryPlatformImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: AzureGroupContainerToGCPArtifactRegistryPlatformImageRelProperties = (
        AzureGroupContainerToGCPArtifactRegistryPlatformImageRelProperties()
    )


@dataclass(frozen=True)
class AzureGroupContainerSchema(CartographyNodeSchema):
    label: str = "AzureGroupContainer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Container"])
    properties: AzureGroupContainerNodeProperties = AzureGroupContainerNodeProperties()
    sub_resource_relationship: AzureGroupContainerToSubscriptionRel = (
        AzureGroupContainerToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureContainerInstanceToGroupContainerRel(),
            AzureGroupContainerToECRImageRel(),
            AzureGroupContainerToGitLabContainerImageRel(),
            AzureGroupContainerToGCPArtifactRegistryContainerImageRel(),
            AzureGroupContainerToGCPArtifactRegistryPlatformImageRel(),
        ],
    )
