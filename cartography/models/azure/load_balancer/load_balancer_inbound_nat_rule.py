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
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    protocol: PropertyRef = PropertyRef("protocol")
    frontend_port: PropertyRef = PropertyRef("frontend_port")
    backend_port: PropertyRef = PropertyRef("backend_port")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerInboundNatRuleToLBRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerInboundNatRuleToLBRel(CartographyRelSchema):
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
