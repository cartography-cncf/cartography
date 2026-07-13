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
    id: PropertyRef = PropertyRef("id")
    address: PropertyRef = PropertyRef("address")
    is_ipv6: PropertyRef = PropertyRef("is_ipv6")
    tags: PropertyRef = PropertyRef("tags")
    region: PropertyRef = PropertyRef("region")
    zone: PropertyRef = PropertyRef("zone")
    source_private_network_id: PropertyRef = PropertyRef("source.private_network_id")
    source_subnet_id: PropertyRef = PropertyRef("source.subnet_id")
    source_vpc_id: PropertyRef = PropertyRef("source.vpc_id")
    # The resource the IP is currently attached to (e.g. an instance private NIC).
    resource_type: PropertyRef = PropertyRef("resource.type_")
    resource_id: PropertyRef = PropertyRef("resource.id")
    resource_name: PropertyRef = PropertyRef("resource.name")
    resource_mac_address: PropertyRef = PropertyRef("resource.mac_address")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayIPToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayIP)
class ScalewayIPToProjectRel(CartographyRelSchema):
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
    label: str = "ScalewayIP"
    properties: ScalewayIPProperties = ScalewayIPProperties()
    sub_resource_relationship: ScalewayIPToProjectRel = ScalewayIPToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayIPToSubnetRel(),
        ]
    )
