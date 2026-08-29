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
class AzureApplicationGatewayRuleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Azure resource ID of the application gateway request routing rule.",
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the application gateway request routing rule."
    )
    rule_type: PropertyRef = PropertyRef(
        "rule_type", description="Routing type of the rule."
    )
    priority: PropertyRef = PropertyRef(
        "priority", description="Evaluation priority of the routing rule."
    )
    url_path_map_id: PropertyRef = PropertyRef(
        "url_path_map_id",
        description="Azure resource ID of the URL path map used by the rule.",
    )
    listener_id: PropertyRef = PropertyRef(
        "listener_id",
        description="Azure resource ID of the HTTP listener used by the rule.",
    )
    listener_protocol: PropertyRef = PropertyRef(
        "listener_protocol", description="Protocol accepted by the associated listener."
    )
    listener_port: PropertyRef = PropertyRef(
        "listener_port", description="Port accepted by the associated listener."
    )
    listener_host_name: PropertyRef = PropertyRef(
        "listener_host_name",
        description="Host name accepted by the associated listener.",
    )
    listener_host_names: PropertyRef = PropertyRef(
        "listener_host_names",
        description="Host names accepted by the associated listener.",
    )
    listener_require_server_name_indication: PropertyRef = PropertyRef(
        "listener_require_server_name_indication",
        description="Whether the listener requires Server Name Indication.",
    )
    listener_ssl_certificate_id: PropertyRef = PropertyRef(
        "listener_ssl_certificate_id",
        description="Azure resource ID of the listener TLS certificate.",
    )
    backend_http_settings_id: PropertyRef = PropertyRef(
        "backend_http_settings_id",
        description="Azure resource ID of the backend HTTP settings used by the rule.",
    )
    backend_protocol: PropertyRef = PropertyRef(
        "backend_protocol",
        description="Protocol used to communicate with backend targets.",
    )
    backend_port: PropertyRef = PropertyRef(
        "backend_port", description="Port used to communicate with backend targets."
    )
    backend_cookie_based_affinity: PropertyRef = PropertyRef(
        "backend_cookie_based_affinity",
        description="Cookie-based affinity setting for backend traffic.",
    )
    backend_request_timeout: PropertyRef = PropertyRef(
        "backend_request_timeout", description="Backend request timeout in seconds."
    )
    backend_host_name: PropertyRef = PropertyRef(
        "backend_host_name", description="Host name sent to backend targets."
    )
    backend_pick_host_name_from_backend_address: PropertyRef = PropertyRef(
        "backend_pick_host_name_from_backend_address",
        description="Whether the backend host name is derived from the backend address.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayRuleToGatewayRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayRuleToGatewayRel(CartographyRelSchema):
    """An Azure Application Gateway contains the request routing rule."""

    target_node_label: str = "AzureApplicationGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("APPLICATION_GATEWAY_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureApplicationGatewayRuleToGatewayRelProperties = (
        AzureApplicationGatewayRuleToGatewayRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayRuleToFrontendIPRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayRuleToFrontendIPRel(CartographyRelSchema):
    """An application gateway request routing rule uses a frontend IP configuration."""

    target_node_label: str = "AzureApplicationGatewayFrontendIPConfiguration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FRONTEND_IP_ID")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_FRONTEND_IP"
    properties: AzureApplicationGatewayRuleToFrontendIPRelProperties = (
        AzureApplicationGatewayRuleToFrontendIPRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayRuleToBackendPoolRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayRuleToBackendPoolRel(CartographyRelSchema):
    """An application gateway request routing rule routes traffic to a backend pool."""

    target_node_label: str = "AzureApplicationGatewayBackendPool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("BACKEND_POOL_ID")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO"
    properties: AzureApplicationGatewayRuleToBackendPoolRelProperties = (
        AzureApplicationGatewayRuleToBackendPoolRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayRuleToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayRuleToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the application gateway request routing rule as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureApplicationGatewayRuleToSubscriptionRelProperties = (
        AzureApplicationGatewayRuleToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayRuleSchema(CartographyNodeSchema):
    """A request routing rule that directs Azure Application Gateway traffic."""

    label: str = "AzureApplicationGatewayRule"
    properties: AzureApplicationGatewayRuleProperties = (
        AzureApplicationGatewayRuleProperties()
    )
    sub_resource_relationship: AzureApplicationGatewayRuleToSubscriptionRel = (
        AzureApplicationGatewayRuleToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureApplicationGatewayRuleToGatewayRel(),
            AzureApplicationGatewayRuleToFrontendIPRel(),
            AzureApplicationGatewayRuleToBackendPoolRel(),
        ],
    )
