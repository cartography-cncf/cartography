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
class AzureLoadBalancerFrontendIPProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    private_ip_address: PropertyRef = PropertyRef("private_ip_address")
    public_ip_address_id: PropertyRef = PropertyRef("public_ip_address_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerFrontendIPToLBRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerFrontendIPToLBRel(CartographyRelSchema):
    target_node_label: str = "AzureLoadBalancer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("LOAD_BALANCER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureLoadBalancerFrontendIPToLBRelProperties = (
        AzureLoadBalancerFrontendIPToLBRelProperties()
    )


@dataclass(frozen=True)
class AzureLoadBalancerFrontendIPToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerFrontendIPToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureLoadBalancerFrontendIPToSubscriptionRelProperties = (
        AzureLoadBalancerFrontendIPToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureLoadBalancerFrontendIPSchema(CartographyNodeSchema):
    label: str = "AzureLoadBalancerFrontendIPConfiguration"
    properties: AzureLoadBalancerFrontendIPProperties = (
        AzureLoadBalancerFrontendIPProperties()
    )
    sub_resource_relationship: AzureLoadBalancerFrontendIPToSubscriptionRel = (
        AzureLoadBalancerFrontendIPToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureLoadBalancerFrontendIPToLBRel(),
        ]
    )
