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
    id: PropertyRef = PropertyRef(
        "id",
        description="Azure resource ID of the load balancer frontend IP configuration.",
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the load balancer frontend IP configuration."
    )
    private_ip_address: PropertyRef = PropertyRef(
        "private_ip_address", description="Private IP address assigned to the frontend."
    )
    public_ip_address_id: PropertyRef = PropertyRef(
        "public_ip_address_id",
        description="Azure resource ID of the associated public IP address.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerFrontendIPToLBRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerFrontendIPToLBRel(CartographyRelSchema):
    """An Azure Load Balancer contains the frontend IP configuration."""

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
class AzureLoadBalancerFrontendIPToPublicIPRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerFrontendIPToPublicIPRel(CartographyRelSchema):
    """A load balancer frontend IP configuration uses a public IP address."""

    target_node_label: str = "AzurePublicIPAddress"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("public_ip_address_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: AzureLoadBalancerFrontendIPToPublicIPRelProperties = (
        AzureLoadBalancerFrontendIPToPublicIPRelProperties()
    )


@dataclass(frozen=True)
class AzureLoadBalancerFrontendIPToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureLoadBalancerFrontendIPToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the load balancer frontend IP configuration as a resource."""

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
    """A frontend IP configuration that receives traffic for an Azure Load Balancer."""

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
            AzureLoadBalancerFrontendIPToPublicIPRel(),
        ]
    )
