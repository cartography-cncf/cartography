import logging
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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureEventHubProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the event hub."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the event hub.")
    status: PropertyRef = PropertyRef(
        "status", description="Current operational status of the event hub."
    )
    partition_count: PropertyRef = PropertyRef(
        "partition_count", description="Number of partitions in the event hub."
    )
    message_retention_in_days: PropertyRef = PropertyRef(
        "message_retention_in_days",
        description="Number of days that events are retained.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureEventHubToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureEventHubToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the event hub as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureEventHubToSubscriptionRelProperties = (
        AzureEventHubToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureEventHubToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# Other relationship to Namespace
@dataclass(frozen=True)
class AzureEventHubToNamespaceRel(CartographyRelSchema):
    """An Event Hubs namespace contains the event hub."""

    target_node_label: str = "AzureEventHubsNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("namespace_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureEventHubToNamespaceRelProperties = (
        AzureEventHubToNamespaceRelProperties()
    )


@dataclass(frozen=True)
class AzureEventHubSchema(CartographyNodeSchema):
    """An event stream within an Azure Event Hubs namespace."""

    label: str = "AzureEventHub"
    properties: AzureEventHubProperties = AzureEventHubProperties()
    sub_resource_relationship: AzureEventHubToSubscriptionRel = (
        AzureEventHubToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureEventHubToNamespaceRel(),
        ],
    )
