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
class AzureApplicationGatewayBackendHTTPSettingsProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    protocol: PropertyRef = PropertyRef("protocol")
    port: PropertyRef = PropertyRef("port")
    cookie_based_affinity: PropertyRef = PropertyRef("cookie_based_affinity")
    request_timeout: PropertyRef = PropertyRef("request_timeout")
    host_name: PropertyRef = PropertyRef("host_name")
    pick_host_name_from_backend_address: PropertyRef = PropertyRef(
        "pick_host_name_from_backend_address",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayBackendHTTPSettingsToGatewayRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayBackendHTTPSettingsToGatewayRel(CartographyRelSchema):
    target_node_label: str = "AzureApplicationGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("APPLICATION_GATEWAY_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureApplicationGatewayBackendHTTPSettingsToGatewayRelProperties = (
        AzureApplicationGatewayBackendHTTPSettingsToGatewayRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayBackendHTTPSettingsToSubscriptionRelProperties(
    CartographyRelProperties,
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayBackendHTTPSettingsToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: (
        AzureApplicationGatewayBackendHTTPSettingsToSubscriptionRelProperties
    ) = AzureApplicationGatewayBackendHTTPSettingsToSubscriptionRelProperties()


@dataclass(frozen=True)
class AzureApplicationGatewayBackendHTTPSettingsSchema(CartographyNodeSchema):
    label: str = "AzureApplicationGatewayBackendHTTPSettings"
    properties: AzureApplicationGatewayBackendHTTPSettingsProperties = (
        AzureApplicationGatewayBackendHTTPSettingsProperties()
    )
    sub_resource_relationship: (
        AzureApplicationGatewayBackendHTTPSettingsToSubscriptionRel
    ) = AzureApplicationGatewayBackendHTTPSettingsToSubscriptionRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureApplicationGatewayBackendHTTPSettingsToGatewayRel(),
        ],
    )
