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
class AzureApplicationGatewayRequestRoutingRuleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    rule_type: PropertyRef = PropertyRef("rule_type")
    priority: PropertyRef = PropertyRef("priority")
    url_path_map_id: PropertyRef = PropertyRef("url_path_map_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayRequestRoutingRuleToGatewayRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayRequestRoutingRuleToGatewayRel(CartographyRelSchema):
    target_node_label: str = "AzureApplicationGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("APPLICATION_GATEWAY_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureApplicationGatewayRequestRoutingRuleToGatewayRelProperties = (
        AzureApplicationGatewayRequestRoutingRuleToGatewayRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayRequestRoutingRuleToListenerRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayRequestRoutingRuleToListenerRel(CartographyRelSchema):
    target_node_label: str = "AzureApplicationGatewayHTTPListener"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("HTTP_LISTENER_ID")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_LISTENER"
    properties: AzureApplicationGatewayRequestRoutingRuleToListenerRelProperties = (
        AzureApplicationGatewayRequestRoutingRuleToListenerRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayRequestRoutingRuleToBackendPoolRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayRequestRoutingRuleToBackendPoolRel(CartographyRelSchema):
    target_node_label: str = "AzureApplicationGatewayBackendPool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("BACKEND_POOL_ID")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO"
    properties: AzureApplicationGatewayRequestRoutingRuleToBackendPoolRelProperties = (
        AzureApplicationGatewayRequestRoutingRuleToBackendPoolRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayRequestRoutingRuleToBackendHTTPSettingsRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayRequestRoutingRuleToBackendHTTPSettingsRel(
    CartographyRelSchema,
):
    target_node_label: str = "AzureApplicationGatewayBackendHTTPSettings"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("BACKEND_HTTP_SETTINGS_ID")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SETTINGS"
    properties: (
        AzureApplicationGatewayRequestRoutingRuleToBackendHTTPSettingsRelProperties
    ) = AzureApplicationGatewayRequestRoutingRuleToBackendHTTPSettingsRelProperties()


@dataclass(frozen=True)
class AzureApplicationGatewayRequestRoutingRuleToSubscriptionRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayRequestRoutingRuleToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureApplicationGatewayRequestRoutingRuleToSubscriptionRelProperties = (
        AzureApplicationGatewayRequestRoutingRuleToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayRequestRoutingRuleSchema(CartographyNodeSchema):
    label: str = "AzureApplicationGatewayRequestRoutingRule"
    properties: AzureApplicationGatewayRequestRoutingRuleProperties = (
        AzureApplicationGatewayRequestRoutingRuleProperties()
    )
    sub_resource_relationship: (
        AzureApplicationGatewayRequestRoutingRuleToSubscriptionRel
    ) = AzureApplicationGatewayRequestRoutingRuleToSubscriptionRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureApplicationGatewayRequestRoutingRuleToGatewayRel(),
            AzureApplicationGatewayRequestRoutingRuleToListenerRel(),
            AzureApplicationGatewayRequestRoutingRuleToBackendPoolRel(),
            AzureApplicationGatewayRequestRoutingRuleToBackendHTTPSettingsRel(),
        ],
    )
