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
class AzureStorageQueueProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Azure resource ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type", description="Azure resource type.")
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")


@dataclass(frozen=True)
class AzureStorageQueueToStorageQueueServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureStorageQueueService)-[:CONTAINS]->(:AzureStorageQueue)
class AzureStorageQueueToStorageQueueServiceRel(CartographyRelSchema):
    """An Azure Queue Storage service contains the queue."""

    target_node_label: str = "AzureStorageQueueService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("service_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureStorageQueueToStorageQueueServiceRelProperties = (
        AzureStorageQueueToStorageQueueServiceRelProperties()
    )


@dataclass(frozen=True)
class AzureStorageQueueToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureStorageQueue)
class AzureStorageQueueToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the queue as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureStorageQueueToSubscriptionRelProperties = (
        AzureStorageQueueToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureStorageQueueSchema(CartographyNodeSchema):
    """An Azure Storage queue hosted by a queue service."""

    label: str = "AzureStorageQueue"
    properties: AzureStorageQueueProperties = AzureStorageQueueProperties()
    sub_resource_relationship: AzureStorageQueueToSubscriptionRel = (
        AzureStorageQueueToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureStorageQueueToStorageQueueServiceRel(),
        ]
    )
