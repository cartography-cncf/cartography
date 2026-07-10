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
class ScalewaySubnetProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    # The CIDR block (Scaleway names this field `subnet`).
    subnet: PropertyRef = PropertyRef("subnet")
    private_network_id: PropertyRef = PropertyRef("private_network_id")
    vpc_id: PropertyRef = PropertyRef("vpc_id")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewaySubnetToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewaySubnet)
class ScalewaySubnetToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewaySubnetToProjectRelProperties = (
        ScalewaySubnetToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewaySubnetToPrivateNetworkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayPrivateNetwork)-[:HAS]->(:ScalewaySubnet)
class ScalewaySubnetToPrivateNetworkRel(CartographyRelSchema):
    target_node_label: str = "ScalewayPrivateNetwork"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("private_network_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewaySubnetToPrivateNetworkRelProperties = (
        ScalewaySubnetToPrivateNetworkRelProperties()
    )


@dataclass(frozen=True)
class ScalewaySubnetSchema(CartographyNodeSchema):
    label: str = "ScalewaySubnet"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Subnet"])
    properties: ScalewaySubnetProperties = ScalewaySubnetProperties()
    sub_resource_relationship: ScalewaySubnetToProjectRel = ScalewaySubnetToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewaySubnetToPrivateNetworkRel(),
        ]
    )
