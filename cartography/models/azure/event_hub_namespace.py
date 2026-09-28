import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureEventHubsNamespaceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the namespace."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the namespace.")
    location: PropertyRef = PropertyRef(
        "location", description="Azure region where the namespace is deployed."
    )
    sku_name: PropertyRef = PropertyRef(
        "sku_name", description="Name of the namespace pricing SKU."
    )
    sku_tier: PropertyRef = PropertyRef(
        "sku_tier", description="Billing tier of the namespace pricing SKU."
    )
    provisioning_state: PropertyRef = PropertyRef(
        "provisioning_state",
        description="Current provisioning state of the namespace.",
    )
    is_auto_inflate_enabled: PropertyRef = PropertyRef(
        "is_auto_inflate_enabled",
        description="Whether automatic throughput unit scaling is enabled.",
    )
    maximum_throughput_units: PropertyRef = PropertyRef(
        "maximum_throughput_units",
        description="Maximum throughput units allowed when automatic scaling is enabled.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureEventHubsNamespaceToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureEventHubsNamespaceToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the Event Hubs namespace as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureEventHubsNamespaceToSubscriptionRelProperties = (
        AzureEventHubsNamespaceToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureEventHubsNamespaceSchema(CartographyNodeSchema):
    """An Azure Event Hubs namespace that groups event hubs."""

    label: str = "AzureEventHubsNamespace"
    properties: AzureEventHubsNamespaceProperties = AzureEventHubsNamespaceProperties()
    sub_resource_relationship: AzureEventHubsNamespaceToSubscriptionRel = (
        AzureEventHubsNamespaceToSubscriptionRel()
    )
