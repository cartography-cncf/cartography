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
class AzureLoadBalancerRuleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    protocol: PropertyRef = PropertyRef("protocol")
    frontend_port: PropertyRef = PropertyRef("frontend_port")
    backend_port: PropertyRef = PropertyRef("backend_port")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerRuleToLBRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerRuleToLBRel(CartographyRelSchema):
    target_node_label: str = "AzureLoadBalancer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("LOAD_BALANCER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureLoadBalancerRuleToLBRelProperties = (
        AzureLoadBalancerRuleToLBRelProperties()
    )


@dataclass(frozen=True)
class AzureLoadBalancerRuleToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerRuleToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureLoadBalancerRuleToSubscriptionRelProperties = (
        AzureLoadBalancerRuleToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class RuleToFrontendIPRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RuleToFrontendIPRel(CartographyRelSchema):
    target_node_label: str = "AzureLoadBalancerFrontendIPConfiguration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FRONTEND_IP_ID")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_FRONTEND_IP"
    properties: RuleToFrontendIPRelProperties = RuleToFrontendIPRelProperties()


@dataclass(frozen=True)
class RuleToBackendPoolRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RuleToBackendPoolRel(CartographyRelSchema):
    target_node_label: str = "AzureLoadBalancerBackendPool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("BACKEND_POOL_ID")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO"
    properties: RuleToBackendPoolRelProperties = RuleToBackendPoolRelProperties()


@dataclass(frozen=True)
class AzureLoadBalancerRuleSchema(CartographyNodeSchema):
    label: str = "AzureLoadBalancerRule"
    properties: AzureLoadBalancerRuleProperties = AzureLoadBalancerRuleProperties()
    sub_resource_relationship: AzureLoadBalancerRuleToSubscriptionRel = (
        AzureLoadBalancerRuleToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureLoadBalancerRuleToLBRel(),
            RuleToFrontendIPRel(),
            RuleToBackendPoolRel(),
        ],
    )
