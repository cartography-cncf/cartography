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


# --- Node Definitions ---
@dataclass(frozen=True)
class AzureContainerInstanceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    type: PropertyRef = PropertyRef("type")
    provisioning_state: PropertyRef = PropertyRef("provisioning_state")
    ip_address: PropertyRef = PropertyRef("ip_address")
    ip_address_type: PropertyRef = PropertyRef("ip_address_type")
    os_type: PropertyRef = PropertyRef("os_type")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureContainerInstanceToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerInstanceToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureContainerInstanceToSubscriptionRelProperties = (
        AzureContainerInstanceToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureContainerInstanceToSubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureContainerInstanceToSubnetRel(CartographyRelSchema):
    target_node_label: str = "AzureSubnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SUBNET_IDS", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: AzureContainerInstanceToSubnetRelProperties = (
        AzureContainerInstanceToSubnetRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureContainerInstanceSchema(CartographyNodeSchema):
    label: str = "AzureContainerInstance"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Container"])
    properties: AzureContainerInstanceProperties = AzureContainerInstanceProperties()
    sub_resource_relationship: AzureContainerInstanceToSubscriptionRel = (
        AzureContainerInstanceToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureContainerInstanceToSubnetRel(),
        ],
    )
