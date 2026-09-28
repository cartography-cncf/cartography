from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AzureStorageFileServiceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Azure resource ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type", description="Azure resource type.")
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")


@dataclass(frozen=True)
class AzureStorageFileServiceToStorageAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureStorageAccount)-[:USES]->(:AzureStorageFileService)
class AzureStorageFileServiceToStorageAccountRel(CartographyRelSchema):
    """An Azure Storage account uses the file service."""

    target_node_label: str = "AzureStorageAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("storage_account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "USES"
    properties: AzureStorageFileServiceToStorageAccountRelProperties = (
        AzureStorageFileServiceToStorageAccountRelProperties()
    )


@dataclass(frozen=True)
class AzureStorageFileServiceToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureStorageFileService)
class AzureStorageFileServiceToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the file service as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureStorageFileServiceToSubscriptionRelProperties = (
        AzureStorageFileServiceToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureStorageFileServiceSchema(CartographyNodeSchema):
    """The Azure Files service of an Azure Storage account."""

    label: str = "AzureStorageFileService"
    properties: AzureStorageFileServiceProperties = AzureStorageFileServiceProperties()
    sub_resource_relationship: AzureStorageFileServiceToSubscriptionRel = (
        AzureStorageFileServiceToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureStorageFileServiceToStorageAccountRel(),
        ]
    )
