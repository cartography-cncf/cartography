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
class AzureStorageBlobServiceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Azure resource ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type", description="Azure resource type.")
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")


@dataclass(frozen=True)
class AzureStorageBlobServiceToStorageAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureStorageAccount)-[:USES]->(:AzureStorageBlobService)
class AzureStorageBlobServiceToStorageAccountRel(CartographyRelSchema):
    """An Azure Storage account uses the blob service."""

    target_node_label: str = "AzureStorageAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("storage_account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "USES"
    properties: AzureStorageBlobServiceToStorageAccountRelProperties = (
        AzureStorageBlobServiceToStorageAccountRelProperties()
    )


@dataclass(frozen=True)
class AzureStorageBlobServiceToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureStorageBlobService)
class AzureStorageBlobServiceToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the blob service as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureStorageBlobServiceToSubscriptionRelProperties = (
        AzureStorageBlobServiceToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureStorageBlobServiceSchema(CartographyNodeSchema):
    """The Blob Storage service of an Azure Storage account."""

    label: str = "AzureStorageBlobService"
    properties: AzureStorageBlobServiceProperties = AzureStorageBlobServiceProperties()
    sub_resource_relationship: AzureStorageBlobServiceToSubscriptionRel = (
        AzureStorageBlobServiceToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureStorageBlobServiceToStorageAccountRel(),
        ]
    )
