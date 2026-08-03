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
class AzureLoadBalancerBackendPoolProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID of the load balancer backend pool."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the load balancer backend pool."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerBackendPoolToLBRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerBackendPoolToLBRel(CartographyRelSchema):
    """An Azure Load Balancer contains the backend pool."""

    target_node_label: str = "AzureLoadBalancer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("LOAD_BALANCER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureLoadBalancerBackendPoolToLBRelProperties = (
        AzureLoadBalancerBackendPoolToLBRelProperties()
    )


@dataclass(frozen=True)
class AzureLoadBalancerBackendPoolToNICRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerBackendPoolToNICRel(CartographyRelSchema):
    """A load balancer backend pool routes traffic to a network interface."""

    target_node_label: str = "AzureNetworkInterface"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NIC_IDS", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO"
    properties: AzureLoadBalancerBackendPoolToNICRelProperties = (
        AzureLoadBalancerBackendPoolToNICRelProperties()
    )


@dataclass(frozen=True)
class AzureLoadBalancerBackendPoolToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerBackendPoolToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the load balancer backend pool as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureLoadBalancerBackendPoolToSubscriptionRelProperties = (
        AzureLoadBalancerBackendPoolToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureLoadBalancerBackendPoolSchema(CartographyNodeSchema):
    """A collection of backend targets for an Azure Load Balancer."""

    label: str = "AzureLoadBalancerBackendPool"
    properties: AzureLoadBalancerBackendPoolProperties = (
        AzureLoadBalancerBackendPoolProperties()
    )
    sub_resource_relationship: AzureLoadBalancerBackendPoolToSubscriptionRel = (
        AzureLoadBalancerBackendPoolToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureLoadBalancerBackendPoolToLBRel(),
            AzureLoadBalancerBackendPoolToNICRel(),
        ],
    )
