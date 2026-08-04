import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import LOAD_BALANCER

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureApplicationGatewayProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID of the application gateway."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the application gateway."
    )
    location: PropertyRef = PropertyRef(
        "location", description="Azure region containing the application gateway."
    )
    sku_name: PropertyRef = PropertyRef(
        "sku_name", description="Name of the application gateway SKU."
    )
    sku_tier: PropertyRef = PropertyRef(
        "sku_tier", description="Tier of the application gateway SKU."
    )
    sku_capacity: PropertyRef = PropertyRef(
        "sku_capacity",
        description="Configured instance capacity of the application gateway.",
    )
    operational_state: PropertyRef = PropertyRef(
        "operational_state",
        description="Current operational state of the application gateway.",
    )
    provisioning_state: PropertyRef = PropertyRef(
        "provisioning_state",
        description="Current provisioning state of the application gateway.",
    )
    enable_http2: PropertyRef = PropertyRef(
        "enable_http2",
        description="Whether HTTP/2 is enabled for the application gateway.",
    )
    firewall_policy_id: PropertyRef = PropertyRef(
        "firewall_policy_id",
        description="Azure resource ID of the associated firewall policy.",
    )
    subnet_id: PropertyRef = PropertyRef(
        "subnet_id", description="Azure resource ID of the gateway subnet."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the application gateway as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureApplicationGatewayToSubscriptionRelProperties = (
        AzureApplicationGatewayToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewayToSubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayToSubnetRel(CartographyRelSchema):
    """An Azure Application Gateway is deployed in a subnet."""

    target_node_label: str = "AzureSubnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("subnet_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_SUBNET"
    properties: AzureApplicationGatewayToSubnetRelProperties = (
        AzureApplicationGatewayToSubnetRelProperties()
    )


@dataclass(frozen=True)
class AzureApplicationGatewaySchema(CartographyNodeSchema):
    """An Azure Application Gateway that routes web traffic to backend targets."""

    label: str = "AzureApplicationGateway"
    properties: AzureApplicationGatewayProperties = AzureApplicationGatewayProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LOAD_BALANCER])
    sub_resource_relationship: AzureApplicationGatewayToSubscriptionRel = (
        AzureApplicationGatewayToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureApplicationGatewayToSubnetRel(),
        ],
    )
