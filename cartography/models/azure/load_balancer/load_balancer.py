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
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import LOAD_BALANCER

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureLoadBalancerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID of the load balancer."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the load balancer.")
    location: PropertyRef = PropertyRef(
        "location", description="Azure region containing the load balancer."
    )
    sku_name: PropertyRef = PropertyRef(
        "sku_name", description="Name of the load balancer SKU."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the load balancer as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureLoadBalancerToSubscriptionRelProperties = (
        AzureLoadBalancerToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureLoadBalancerSchema(CartographyNodeSchema):
    """An Azure Load Balancer that distributes network traffic across backend targets."""

    label: str = "AzureLoadBalancer"
    properties: AzureLoadBalancerProperties = AzureLoadBalancerProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LOAD_BALANCER])
    sub_resource_relationship: AzureLoadBalancerToSubscriptionRel = (
        AzureLoadBalancerToSubscriptionRel()
    )
