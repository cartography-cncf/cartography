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


@dataclass(frozen=True)
class GCPNetworkInterfaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("nic_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    private_ip: PropertyRef = PropertyRef("networkIP")
    name: PropertyRef = PropertyRef("name")


@dataclass(frozen=True)
class GCPNetworkInterfaceToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPNetworkInterfaceToInstanceRel(CartographyRelSchema):
    target_node_label: str = "GCPInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("instance_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "NETWORK_INTERFACE"
    properties: GCPNetworkInterfaceToInstanceRelProperties = (
        GCPNetworkInterfaceToInstanceRelProperties()
    )


@dataclass(frozen=True)
class GCPNetworkInterfaceToSubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPNetworkInterfaceToSubnetRel(CartographyRelSchema):
    target_node_label: str = "GCPSubnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("subnet_partial_uri"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_SUBNET"
    properties: GCPNetworkInterfaceToSubnetRelProperties = (
        GCPNetworkInterfaceToSubnetRelProperties()
    )


@dataclass(frozen=True)
class GCPNetworkInterfaceToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPNetworkInterfaceToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPNetworkInterfaceToProjectRelProperties = (
        GCPNetworkInterfaceToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPNetworkInterfaceSchema(CartographyNodeSchema):
    label: str = "GCPNetworkInterface"
    properties: GCPNetworkInterfaceNodeProperties = GCPNetworkInterfaceNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["NetworkInterface"])
    sub_resource_relationship: GCPNetworkInterfaceToProjectRel = (
        GCPNetworkInterfaceToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPNetworkInterfaceToInstanceRel(),
            GCPNetworkInterfaceToSubnetRel(),
        ]
    )
