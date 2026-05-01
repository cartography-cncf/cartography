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
class AzureContainerInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    group_id: PropertyRef = PropertyRef("group_id")
    image: PropertyRef = PropertyRef("image")
    image_digest: PropertyRef = PropertyRef("image_digest")
    architecture: PropertyRef = PropertyRef("architecture")
    architecture_normalized: PropertyRef = PropertyRef("architecture_normalized")
    state: PropertyRef = PropertyRef("state")
    cpu_request: PropertyRef = PropertyRef("cpu_request")
    memory_request_gb: PropertyRef = PropertyRef("memory_request_gb")
    cpu_limit: PropertyRef = PropertyRef("cpu_limit")
    memory_limit_gb: PropertyRef = PropertyRef("memory_limit_gb")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerInstanceToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerInstanceToSubscriptionRel(CartographyRelSchema):
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
    target_node_label: str = "ECRImage"
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
class AzureContainerInstanceToGCPArtifactRegistryContainerImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerInstanceToGCPArtifactRegistryContainerImageRel(
    CartographyRelSchema
):
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: (
        AzureContainerInstanceToGCPArtifactRegistryContainerImageRelProperties
    ) = AzureContainerInstanceToGCPArtifactRegistryContainerImageRelProperties()


@dataclass(frozen=True)
class AzureContainerInstanceToGCPArtifactRegistryPlatformImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerInstanceToGCPArtifactRegistryPlatformImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryPlatformImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: (
        AzureContainerInstanceToGCPArtifactRegistryPlatformImageRelProperties
    ) = AzureContainerInstanceToGCPArtifactRegistryPlatformImageRelProperties()


@dataclass(frozen=True)
class AzureContainerInstanceSchema(CartographyNodeSchema):
    label: str = "AzureContainerInstance"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Container"])
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
            AzureContainerInstanceToGCPArtifactRegistryContainerImageRel(),
            AzureContainerInstanceToGCPArtifactRegistryPlatformImageRel(),
        ],
    )
