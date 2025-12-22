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
class AzureNetworkInterfaceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    mac_address: PropertyRef = PropertyRef("mac_address")
    private_ip_addresses: PropertyRef = PropertyRef("private_ip_addresses")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureNetworkInterfaceToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureNetworkInterfaceToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureNetworkInterfaceToSubscriptionRelProperties = (
        AzureNetworkInterfaceToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureNetworkInterfaceToVirtualMachineRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureNetworkInterfaceToVirtualMachineRel(CartographyRelSchema):
    target_node_label: str = "AzureVirtualMachine"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VIRTUAL_MACHINE_ID")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: AzureNetworkInterfaceToVirtualMachineRelProperties = (
        AzureNetworkInterfaceToVirtualMachineRelProperties()
    )


@dataclass(frozen=True)
class AzureNetworkInterfaceToSubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureNetworkInterfaceToSubnetRel(CartographyRelSchema):
    target_node_label: str = "AzureSubnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SUBNET_IDS", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: AzureNetworkInterfaceToSubnetRelProperties = (
        AzureNetworkInterfaceToSubnetRelProperties()
    )


@dataclass(frozen=True)
class AzureNetworkInterfaceToPublicIPRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureNetworkInterfaceToPublicIPRel(CartographyRelSchema):
    target_node_label: str = "AzurePublicIPAddress"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PUBLIC_IP_IDS", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: AzureNetworkInterfaceToPublicIPRelProperties = (
        AzureNetworkInterfaceToPublicIPRelProperties()
    )


@dataclass(frozen=True)
class AzureNetworkInterfaceSchema(CartographyNodeSchema):
    label: str = "AzureNetworkInterface"
    properties: AzureNetworkInterfaceProperties = AzureNetworkInterfaceProperties()
    sub_resource_relationship: AzureNetworkInterfaceToSubscriptionRel = (
        AzureNetworkInterfaceToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureNetworkInterfaceToVirtualMachineRel(),
            AzureNetworkInterfaceToSubnetRel(),
            AzureNetworkInterfaceToPublicIPRel(),
        ],
    )
