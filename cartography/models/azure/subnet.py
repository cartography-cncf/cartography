import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import SUBNET

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureSubnetProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the subnet."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the subnet.")
    address_prefix: PropertyRef = PropertyRef(
        "address_prefix",
        description="IPv4 or IPv6 address prefix assigned to the subnet.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSubnetToVNetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSubnetToVNetRel(CartographyRelSchema):
    """An Azure virtual network contains the subnet."""

    target_node_label: str = "AzureVirtualNetwork"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VNET_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureSubnetToVNetRelProperties = AzureSubnetToVNetRelProperties()


@dataclass(frozen=True)
class AzureSubnetToNSGRelProperties(CartographyRelProperties):
    """
    The properties for the relationship from an AzureSubnet to an AzureNetworkSecurityGroup.
    These must be defined so the loader can save them on the relationship.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )


@dataclass(frozen=True)
class AzureSubnetToNSGRel(CartographyRelSchema):
    """An Azure subnet is associated with a network security group."""

    source_node_label: str = "AzureSubnet"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("NODE_ID")},
    )
    target_node_label: str = "AzureNetworkSecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NSG_ID")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: AzureSubnetToNSGRelProperties = AzureSubnetToNSGRelProperties()


@dataclass(frozen=True)
class AzureSubnetToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSubnetToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the subnet as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSubnetToSubscriptionRelProperties = (
        AzureSubnetToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureSubnetSchema(CartographyNodeSchema):
    """A subnet within an Azure virtual network."""

    label: str = "AzureSubnet"
    properties: AzureSubnetProperties = AzureSubnetProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SUBNET])
    sub_resource_relationship: AzureSubnetToSubscriptionRel = (
        AzureSubnetToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureSubnetToVNetRel(),
        ],
    )
