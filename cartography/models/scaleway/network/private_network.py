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


@dataclass(frozen=True)
class ScalewayPrivateNetworkProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Private Network unique ID.")
    name: PropertyRef = PropertyRef("name", description="Private Network name.")
    region: PropertyRef = PropertyRef(
        "region", description="Region the Private Network lives in."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags associated with the Private Network."
    )
    vpc_id: PropertyRef = PropertyRef(
        "vpc_id", description="ID of the VPC the Private Network belongs to."
    )
    dhcp_enabled: PropertyRef = PropertyRef(
        "dhcp_enabled", description="True if managed DHCP is enabled."
    )
    default_route_propagation_enabled: PropertyRef = PropertyRef(
        "default_route_propagation_enabled",
        description="True if the default route is propagated.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Private Network creation date."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Private Network last update date."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayPrivateNetworkToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayPrivateNetwork)
class ScalewayPrivateNetworkToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayPrivateNetwork` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayPrivateNetworkToProjectRelProperties = (
        ScalewayPrivateNetworkToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayPrivateNetworkToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayVpc)-[:HAS]->(:ScalewayPrivateNetwork)
class ScalewayPrivateNetworkToVpcRel(CartographyRelSchema):
    """Connects `ScalewayVpc` to `ScalewayPrivateNetwork` through `HAS`."""

    target_node_label: str = "ScalewayVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vpc_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayPrivateNetworkToVpcRelProperties = (
        ScalewayPrivateNetworkToVpcRelProperties()
    )


@dataclass(frozen=True)
class ScalewayPrivateNetworkSchema(CartographyNodeSchema):
    """A Private Network is a layer-2 network within a VPC that Instances and other
    resources attach to.
    """

    label: str = "ScalewayPrivateNetwork"
    properties: ScalewayPrivateNetworkProperties = ScalewayPrivateNetworkProperties()
    sub_resource_relationship: ScalewayPrivateNetworkToProjectRel = (
        ScalewayPrivateNetworkToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayPrivateNetworkToVpcRel(),
        ]
    )
