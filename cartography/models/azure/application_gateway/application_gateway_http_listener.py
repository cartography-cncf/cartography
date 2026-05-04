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
class AzureApplicationGatewayHTTPListenerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    protocol: PropertyRef = PropertyRef("protocol")
    frontend_port: PropertyRef = PropertyRef("frontend_port")
    host_name: PropertyRef = PropertyRef("host_name")
    host_names: PropertyRef = PropertyRef("host_names")
    require_server_name_indication: PropertyRef = PropertyRef(
        "require_server_name_indication",
    )
    ssl_certificate_id: PropertyRef = PropertyRef("ssl_certificate_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayHTTPListenerToGatewayRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayHTTPListenerToGatewayRel(CartographyRelSchema):
    target_node_label: str = "AzureApplicationGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("APPLICATION_GATEWAY_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureApplicationGatewayHTTPListenerToGatewayRelProperties = (
        AzureApplicationGatewayHTTPListenerToGatewayRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayHTTPListenerToFrontendIPRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayHTTPListenerToFrontendIPRel(CartographyRelSchema):
    target_node_label: str = "AzureApplicationGatewayFrontendIPConfiguration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FRONTEND_IP_ID")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_FRONTEND_IP"
    properties: AzureApplicationGatewayHTTPListenerToFrontendIPRelProperties = (
        AzureApplicationGatewayHTTPListenerToFrontendIPRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayHTTPListenerToSubscriptionRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayHTTPListenerToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureApplicationGatewayHTTPListenerToSubscriptionRelProperties = (
        AzureApplicationGatewayHTTPListenerToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayHTTPListenerSchema(CartographyNodeSchema):
    label: str = "AzureApplicationGatewayHTTPListener"
    properties: AzureApplicationGatewayHTTPListenerProperties = (
        AzureApplicationGatewayHTTPListenerProperties()
    )
    sub_resource_relationship: AzureApplicationGatewayHTTPListenerToSubscriptionRel = (
        AzureApplicationGatewayHTTPListenerToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureApplicationGatewayHTTPListenerToGatewayRel(),
            AzureApplicationGatewayHTTPListenerToFrontendIPRel(),
        ],
    )
