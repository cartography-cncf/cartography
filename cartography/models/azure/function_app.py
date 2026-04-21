import logging
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

logger = logging.getLogger(__name__)


# --- Node Definitions ---
@dataclass(frozen=True)
class AzureFunctionAppProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    kind: PropertyRef = PropertyRef("kind")
    location: PropertyRef = PropertyRef("location")
    state: PropertyRef = PropertyRef("state")
    default_host_name: PropertyRef = PropertyRef("default_host_name")
    https_only: PropertyRef = PropertyRef("https_only")
    is_container: PropertyRef = PropertyRef("is_container")
    deployment_type: PropertyRef = PropertyRef("deployment_type")
    image_uri: PropertyRef = PropertyRef("image_uri")
    image_digest: PropertyRef = PropertyRef("image_digest")
    architecture_normalized: PropertyRef = PropertyRef("architecture_normalized")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureFunctionAppToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFunctionAppToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureFunctionAppToSubscriptionRelProperties = (
        AzureFunctionAppToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureFunctionAppToECRImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFunctionAppToECRImageRel(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: AzureFunctionAppToECRImageRelProperties = (
        AzureFunctionAppToECRImageRelProperties()
    )


@dataclass(frozen=True)
class AzureFunctionAppToGitLabContainerImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFunctionAppToGitLabContainerImageRel(CartographyRelSchema):
    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: AzureFunctionAppToGitLabContainerImageRelProperties = (
        AzureFunctionAppToGitLabContainerImageRelProperties()
    )


@dataclass(frozen=True)
class AzureFunctionAppToGCPArtifactRegistryContainerImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureFunctionAppToGCPArtifactRegistryContainerImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: AzureFunctionAppToGCPArtifactRegistryContainerImageRelProperties = (
        AzureFunctionAppToGCPArtifactRegistryContainerImageRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureFunctionAppSchema(CartographyNodeSchema):
    """
    The schema for an Azure Function App.
    """

    label: str = "AzureFunctionApp"
    properties: AzureFunctionAppProperties = AzureFunctionAppProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Function"])
    sub_resource_relationship: AzureFunctionAppToSubscriptionRel = (
        AzureFunctionAppToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureFunctionAppToECRImageRel(),
            AzureFunctionAppToGitLabContainerImageRel(),
            AzureFunctionAppToGCPArtifactRegistryContainerImageRel(),
        ],
    )
