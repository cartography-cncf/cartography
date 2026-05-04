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
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    rule_type: PropertyRef = PropertyRef("rule_type")
    priority: PropertyRef = PropertyRef("priority")
    url_path_map_id: PropertyRef = PropertyRef("url_path_map_id")
    listener_id: PropertyRef = PropertyRef("listener_id")
    listener_protocol: PropertyRef = PropertyRef("listener_protocol")
    listener_port: PropertyRef = PropertyRef("listener_port")
    listener_host_name: PropertyRef = PropertyRef("listener_host_name")
    listener_host_names: PropertyRef = PropertyRef("listener_host_names")
    listener_require_server_name_indication: PropertyRef = PropertyRef(
        "listener_require_server_name_indication",
    )
    listener_ssl_certificate_id: PropertyRef = PropertyRef(
        "listener_ssl_certificate_id"
    )
    backend_http_settings_id: PropertyRef = PropertyRef("backend_http_settings_id")
    backend_protocol: PropertyRef = PropertyRef("backend_protocol")
    backend_port: PropertyRef = PropertyRef("backend_port")
    backend_cookie_based_affinity: PropertyRef = PropertyRef(
        "backend_cookie_based_affinity",
    )
    backend_request_timeout: PropertyRef = PropertyRef("backend_request_timeout")
    backend_host_name: PropertyRef = PropertyRef("backend_host_name")
    backend_pick_host_name_from_backend_address: PropertyRef = PropertyRef(
        "backend_pick_host_name_from_backend_address",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayRuleToGatewayRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayRuleToGatewayRel(CartographyRelSchema):
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
