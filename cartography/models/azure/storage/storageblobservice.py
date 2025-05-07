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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type")
    name: PropertyRef = PropertyRef("name")


@dataclass(frozen=True)
class AzureStorageBlobServiceToStorageAccountProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureStorageAccount)-[:USES]->(:AzureStorageBlobService)
class AzureStorageBlobServiceToStorageAccountRel(CartographyRelSchema):
    target_node_label: str = "AzureStorageAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("storage_account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "USES"
    properties: AzureStorageBlobServiceToStorageAccountProperties = (
        AzureStorageBlobServiceToStorageAccountProperties()
    )


@dataclass(frozen=True)
class AzureStorageBlobServiceToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureStorageBlobService)
class AzureStorageBlobServiceToSubscriptionRel(CartographyRelSchema):
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
