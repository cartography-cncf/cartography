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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type")
    name: PropertyRef = PropertyRef("name")


@dataclass(frozen=True)
class AzureStorageFileServiceToStorageAccountProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureStorageAccount)-[:USES]->(:AzureStorageFileService)
class AzureStorageFileServiceToStorageAccountRel(CartographyRelSchema):
    target_node_label: str = "AzureStorageAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("storage_account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "USES"
    properties: AzureStorageFileServiceToStorageAccountProperties = (
        AzureStorageFileServiceToStorageAccountProperties()
    )


@dataclass(frozen=True)
class AzureStorageFileServiceToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureStorageFileService)
class AzureStorageFileServiceToSubscriptionRel(CartographyRelSchema):
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
