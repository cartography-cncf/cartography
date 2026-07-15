from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ScalewayFlexibleIpProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Flexible IP ID")
    address: PropertyRef = PropertyRef("address", description="IP address")
    reverse: PropertyRef = PropertyRef("reverse", description="Reverse DNS")
    tags: PropertyRef = PropertyRef("tags", description="Tags for the IP")
    type: PropertyRef = PropertyRef(
        "type",
        description="Type of IP (`unknown_iptype`, `routed_ipv4`, `routed_ipv6`)",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="State of the IP (`unknown_state`, `detached`, `attached`, `pending`, `error`)",
    )
    prefix: PropertyRef = PropertyRef("prefix", description="IP Network")
    ipam_id: PropertyRef = PropertyRef("ipam_id", description="IPAM ID (UUI Format)")
    zone: PropertyRef = PropertyRef("zone", description="AZ of the IP")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayFlexibleIpToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayFlexibleIp)
class ScalewayFlexibleIpToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayFlexibleIp` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayFlexibleIpToProjectRelProperties = (
        ScalewayFlexibleIpToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayFlexibleIpSchema(CartographyNodeSchema):
    """Flexible IP addresses are public IP addresses that you can hold independently of any
    Instance. By default, a Scaleway Instance's public IP is also a flexible IP address.
    """

    label: str = "ScalewayFlexibleIp"
    properties: ScalewayFlexibleIpProperties = ScalewayFlexibleIpProperties()
    sub_resource_relationship: ScalewayFlexibleIpToProjectRel = (
        ScalewayFlexibleIpToProjectRel()
    )
