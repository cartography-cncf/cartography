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
class AzureStorageQueueServiceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type")
    name: PropertyRef = PropertyRef("name")


@dataclass(frozen=True)
class AzureStorageQueueServiceToStorageAccountProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureStorageAccount)-[:USES]->(:AzureStorageQueueService)
class AzureStorageQueueServiceToStorageAccountRel(CartographyRelSchema):
    target_node_label: str = "AzureStorageAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("storage_account_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "USES"
    properties: AzureStorageQueueServiceToStorageAccountProperties = (
        AzureStorageQueueServiceToStorageAccountProperties()
    )


@dataclass(frozen=True)
class AzureStorageQueueServiceToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureStorageQueueService)
class AzureStorageQueueServiceToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureStorageQueueServiceToSubscriptionRelProperties = (
        AzureStorageQueueServiceToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureStorageQueueServiceSchema(CartographyNodeSchema):
    label: str = "AzureStorageQueueService"
    properties: AzureStorageQueueServiceProperties = (
        AzureStorageQueueServiceProperties()
    )
    sub_resource_relationship: AzureStorageQueueServiceToSubscriptionRel = (
        AzureStorageQueueServiceToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureStorageQueueServiceToStorageAccountRel(),
        ]
    )
