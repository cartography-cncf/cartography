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
class AzureLoadBalancerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    sku_name: PropertyRef = PropertyRef("sku_name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerToSubscriptionRel(CartographyRelSchema):
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
    label: str = "AzureLoadBalancer"
    properties: AzureLoadBalancerProperties = AzureLoadBalancerProperties()
    sub_resource_relationship: AzureLoadBalancerToSubscriptionRel = (
        AzureLoadBalancerToSubscriptionRel()
    )
