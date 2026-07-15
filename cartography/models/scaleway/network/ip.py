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
class ScalewayIPProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="IP unique ID.")
    address: PropertyRef = PropertyRef(
        "address", description="The IP address (CIDR notation)."
    )
    is_ipv6: PropertyRef = PropertyRef(
        "is_ipv6", description="True if the address is IPv6."
    )
    tags: PropertyRef = PropertyRef("tags", description="Tags associated with the IP.")
    region: PropertyRef = PropertyRef("region", description="Region the IP lives in.")
    zone: PropertyRef = PropertyRef(
        "zone", description="Zone the IP lives in (when zonal)."
    )
    source_private_network_id: PropertyRef = PropertyRef(
        "source.private_network_id",
        description="ID of the Private Network the IP was booked in.",
    )
    source_subnet_id: PropertyRef = PropertyRef(
        "source.subnet_id", description="ID of the subnet the IP was booked in."
    )
    source_vpc_id: PropertyRef = PropertyRef(
        "source.vpc_id", description="ID of the VPC the IP was booked in."
    )
    # The resource the IP is currently attached to (e.g. an instance private NIC).
    resource_type: PropertyRef = PropertyRef(
        "resource.type_",
        description="Type of resource the IP is attached to (e.g. `instance_private_nic`).",
    )
    resource_id: PropertyRef = PropertyRef(
        "resource.id", description="ID of the resource the IP is attached to."
    )
    resource_name: PropertyRef = PropertyRef(
        "resource.name", description="Name of the resource the IP is attached to."
    )
    resource_mac_address: PropertyRef = PropertyRef(
        "resource.mac_address",
        description="MAC address of the resource the IP is attached to.",
    )
    created_at: PropertyRef = PropertyRef("created_at", description="IP creation date.")
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="IP last update date."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayIPToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayIP)
class ScalewayIPToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayIP` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayIPToProjectRelProperties = ScalewayIPToProjectRelProperties()


@dataclass(frozen=True)
class ScalewayIPToSubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewaySubnet)-[:HAS]->(:ScalewayIP)
# The IPAM list API populates `source.subnet_id` (not `private_network_id`) for
# private-network IPs, so we attach the IP to its subnet; the private network is
# reachable transitively via (:ScalewayPrivateNetwork)-[:HAS]->(:ScalewaySubnet).
class ScalewayIPToSubnetRel(CartographyRelSchema):
    """Connects `ScalewaySubnet` to `ScalewayIP` through `HAS`."""

    target_node_label: str = "ScalewaySubnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("subnet_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayIPToSubnetRelProperties = ScalewayIPToSubnetRelProperties()


# TODO: link (:ScalewayIP)-[:IDENTIFIES]->(resource). `resource.id` points at the
# attached object (e.g. an instance private NIC, not the server itself), so the
# match target varies by `resource.type_`; defer until those resources are modeled.


@dataclass(frozen=True)
class ScalewayIPSchema(CartographyNodeSchema):
    """An IP is an IPAM-managed IP address (IPv4 or IPv6) allocated within a Private
    Network and optionally attached to a resource.
    """

    label: str = "ScalewayIP"
    properties: ScalewayIPProperties = ScalewayIPProperties()
    sub_resource_relationship: ScalewayIPToProjectRel = ScalewayIPToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayIPToSubnetRel(),
        ]
    )
