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
class AzureLoadBalancerInboundNatRuleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID of the inbound NAT rule."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the inbound NAT rule.")
    protocol: PropertyRef = PropertyRef(
        "protocol", description="Transport protocol used by the inbound NAT rule."
    )
    frontend_port: PropertyRef = PropertyRef(
        "frontend_port", description="Frontend port that receives inbound traffic."
    )
    backend_port: PropertyRef = PropertyRef(
        "backend_port",
        description="Backend port to which inbound traffic is forwarded.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerInboundNatRuleToLBRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerInboundNatRuleToLBRel(CartographyRelSchema):
    """An Azure Load Balancer contains the inbound NAT rule."""

    target_node_label: str = "AzureLoadBalancer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("LOAD_BALANCER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureLoadBalancerInboundNatRuleToLBRelProperties = (
        AzureLoadBalancerInboundNatRuleToLBRelProperties()
    )


@dataclass(frozen=True)
class AzureLoadBalancerInboundNatRuleToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerInboundNatRuleToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the inbound NAT rule as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureLoadBalancerInboundNatRuleToSubscriptionRelProperties = (
        AzureLoadBalancerInboundNatRuleToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureLoadBalancerInboundNatRuleSchema(CartographyNodeSchema):
    """An inbound NAT rule that forwards Azure Load Balancer traffic to a backend target."""

    label: str = "AzureLoadBalancerInboundNatRule"
    properties: AzureLoadBalancerInboundNatRuleProperties = (
        AzureLoadBalancerInboundNatRuleProperties()
    )
    sub_resource_relationship: AzureLoadBalancerInboundNatRuleToSubscriptionRel = (
        AzureLoadBalancerInboundNatRuleToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureLoadBalancerInboundNatRuleToLBRel(),
        ]
    )
