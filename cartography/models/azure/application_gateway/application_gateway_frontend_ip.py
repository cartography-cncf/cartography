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
class AzureApplicationGatewayFrontendIPProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    private_ip_address: PropertyRef = PropertyRef("private_ip_address")
    private_ip_allocation_method: PropertyRef = PropertyRef(
        "private_ip_allocation_method",
    )
    public_ip_address_id: PropertyRef = PropertyRef("public_ip_address_id")
    subnet_id: PropertyRef = PropertyRef("subnet_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayFrontendIPToGatewayRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayFrontendIPToGatewayRel(CartographyRelSchema):
    target_node_label: str = "AzureApplicationGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("APPLICATION_GATEWAY_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureApplicationGatewayFrontendIPToGatewayRelProperties = (
        AzureApplicationGatewayFrontendIPToGatewayRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayFrontendIPToPublicIPRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayFrontendIPToPublicIPRel(CartographyRelSchema):
    target_node_label: str = "AzurePublicIPAddress"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("public_ip_address_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: AzureApplicationGatewayFrontendIPToPublicIPRelProperties = (
        AzureApplicationGatewayFrontendIPToPublicIPRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayFrontendIPToSubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayFrontendIPToSubnetRel(CartographyRelSchema):
    target_node_label: str = "AzureSubnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("subnet_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_SUBNET"
    properties: AzureApplicationGatewayFrontendIPToSubnetRelProperties = (
        AzureApplicationGatewayFrontendIPToSubnetRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayFrontendIPToSubscriptionRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayFrontendIPToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureApplicationGatewayFrontendIPToSubscriptionRelProperties = (
        AzureApplicationGatewayFrontendIPToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayFrontendIPSchema(CartographyNodeSchema):
    label: str = "AzureApplicationGatewayFrontendIPConfiguration"
    properties: AzureApplicationGatewayFrontendIPProperties = (
        AzureApplicationGatewayFrontendIPProperties()
    )
    sub_resource_relationship: AzureApplicationGatewayFrontendIPToSubscriptionRel = (
        AzureApplicationGatewayFrontendIPToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureApplicationGatewayFrontendIPToGatewayRel(),
            AzureApplicationGatewayFrontendIPToPublicIPRel(),
            AzureApplicationGatewayFrontendIPToSubnetRel(),
        ],
    )
