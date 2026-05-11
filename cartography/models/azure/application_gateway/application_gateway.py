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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureApplicationGatewayProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    sku_name: PropertyRef = PropertyRef("sku_name")
    sku_tier: PropertyRef = PropertyRef("sku_tier")
    sku_capacity: PropertyRef = PropertyRef("sku_capacity")
    operational_state: PropertyRef = PropertyRef("operational_state")
    provisioning_state: PropertyRef = PropertyRef("provisioning_state")
    enable_http2: PropertyRef = PropertyRef("enable_http2")
    firewall_policy_id: PropertyRef = PropertyRef("firewall_policy_id")
    subnet_id: PropertyRef = PropertyRef("subnet_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureApplicationGatewayToSubscriptionRel(CartographyRelSchema):
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
    label: str = "AzureApplicationGateway"
    properties: AzureApplicationGatewayProperties = AzureApplicationGatewayProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["LoadBalancer"])
    sub_resource_relationship: AzureApplicationGatewayToSubscriptionRel = (
        AzureApplicationGatewayToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureApplicationGatewayToSubnetRel(),
        ],
    )
