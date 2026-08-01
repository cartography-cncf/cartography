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
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID of the load balancing rule."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the load balancing rule."
    )
    protocol: PropertyRef = PropertyRef(
        "protocol", description="Transport protocol used by the load balancing rule."
    )
    frontend_port: PropertyRef = PropertyRef(
        "frontend_port", description="Frontend port on which the rule receives traffic."
    )
    backend_port: PropertyRef = PropertyRef(
        "backend_port",
        description="Backend port to which the rule distributes traffic.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerRuleToLBRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerRuleToLBRel(CartographyRelSchema):
    """An Azure Load Balancer contains the load balancing rule."""

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
    """An Azure subscription contains the load balancing rule as a resource."""

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
    """A load balancing rule uses a frontend IP configuration."""

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
    """A load balancing rule routes traffic to a backend pool."""

    target_node_label: str = "AzureLoadBalancerBackendPool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("BACKEND_POOL_ID")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO"
    properties: RuleToBackendPoolRelProperties = RuleToBackendPoolRelProperties()


@dataclass(frozen=True)
class AzureLoadBalancerRuleSchema(CartographyNodeSchema):
    """A rule that distributes Azure Load Balancer traffic across a backend pool."""

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
