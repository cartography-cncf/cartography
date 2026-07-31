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
class AzureApplicationGatewayBackendPoolProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID of the application gateway backend pool."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the application gateway backend pool."
    )
    fqdns: PropertyRef = PropertyRef(
        "fqdns", description="Fully qualified domain names of backend targets."
    )
    ip_addresses: PropertyRef = PropertyRef(
        "ip_addresses", description="IP addresses of backend targets."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayBackendPoolToGatewayRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayBackendPoolToGatewayRel(CartographyRelSchema):
    """An Azure Application Gateway contains the backend pool."""

    target_node_label: str = "AzureApplicationGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("APPLICATION_GATEWAY_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureApplicationGatewayBackendPoolToGatewayRelProperties = (
        AzureApplicationGatewayBackendPoolToGatewayRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayBackendPoolToNICRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayBackendPoolToNICRel(CartographyRelSchema):
    """An application gateway backend pool routes traffic to a network interface."""

    target_node_label: str = "AzureNetworkInterface"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NIC_IDS", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO"
    properties: AzureApplicationGatewayBackendPoolToNICRelProperties = (
        AzureApplicationGatewayBackendPoolToNICRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayBackendPoolToPublicIPRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayBackendPoolToPublicIPRel(CartographyRelSchema):
    """An application gateway backend pool routes traffic to a public IP address."""

    target_node_label: str = "AzurePublicIPAddress"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ip_address": PropertyRef("ip_addresses", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO"
    properties: AzureApplicationGatewayBackendPoolToPublicIPRelProperties = (
        AzureApplicationGatewayBackendPoolToPublicIPRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayBackendPoolToDNSRecordRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayBackendPoolToDNSRecordRel(CartographyRelSchema):
    """An application gateway backend pool routes traffic to a DNS record."""

    target_node_label: str = "DNSRecord"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("fqdns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO"
    properties: AzureApplicationGatewayBackendPoolToDNSRecordRelProperties = (
        AzureApplicationGatewayBackendPoolToDNSRecordRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayBackendPoolToSubscriptionRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayBackendPoolToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the application gateway backend pool as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureApplicationGatewayBackendPoolToSubscriptionRelProperties = (
        AzureApplicationGatewayBackendPoolToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayBackendPoolSchema(CartographyNodeSchema):
    """A collection of backend targets for an Azure Application Gateway."""

    label: str = "AzureApplicationGatewayBackendPool"
    properties: AzureApplicationGatewayBackendPoolProperties = (
        AzureApplicationGatewayBackendPoolProperties()
    )
    sub_resource_relationship: AzureApplicationGatewayBackendPoolToSubscriptionRel = (
        AzureApplicationGatewayBackendPoolToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureApplicationGatewayBackendPoolToGatewayRel(),
            AzureApplicationGatewayBackendPoolToNICRel(),
            AzureApplicationGatewayBackendPoolToPublicIPRel(),
            AzureApplicationGatewayBackendPoolToDNSRecordRel(),
        ],
    )
