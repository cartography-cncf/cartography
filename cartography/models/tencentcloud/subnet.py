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
from cartography.models.ontology.labels import SUBNET


@dataclass(frozen=True)
class TencentCloudSubnetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Subnet ID, e.g. `subnet-bthucmmy`."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the subnet.")
    region: PropertyRef = PropertyRef(
        "region", extra_index=True, description="Region the subnet is in."
    )
    zone: PropertyRef = PropertyRef(
        "zone", description="Availability zone the subnet is in."
    )
    vpc_id: PropertyRef = PropertyRef(
        "vpc_id", description="ID of the VPC that contains the subnet."
    )
    cidr_block: PropertyRef = PropertyRef(
        "cidr_block", description="IPv4 CIDR block of the subnet."
    )
    ipv6_cidr_block: PropertyRef = PropertyRef(
        "ipv6_cidr_block", description="IPv6 CIDR block of the subnet."
    )
    is_default: PropertyRef = PropertyRef(
        "is_default", description="`True` for a default subnet."
    )
    route_table_id: PropertyRef = PropertyRef(
        "route_table_id",
        description="ID of the route table associated with the subnet.",
    )
    network_acl_id: PropertyRef = PropertyRef(
        "network_acl_id",
        description="ID of the network ACL associated with the subnet.",
    )
    available_ip_address_count: PropertyRef = PropertyRef(
        "available_ip_address_count", description="Number of unused IPv4 addresses."
    )
    total_ip_address_count: PropertyRef = PropertyRef(
        "total_ip_address_count", description="Total number of IPv4 addresses."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags on the subnet, as `key:value` strings."
    )
    created_time: PropertyRef = PropertyRef(
        "created_time", description="Time the subnet was created."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TencentCloudSubnetToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudAccount)-[:RESOURCE]->(:TencentCloudSubnet)
class TencentCloudSubnetToAccountRel(CartographyRelSchema):
    """Connects a `TencentCloudAccount` to its subnets."""

    target_node_label: str = "TencentCloudAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TencentCloudSubnetToAccountRelProperties = (
        TencentCloudSubnetToAccountRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudSubnetToVPCRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudSubnet)-[:PART_OF_VPC]->(:TencentCloudVPC)
class TencentCloudSubnetToVPCRel(CartographyRelSchema):
    """Connects a subnet to the VPC that contains it."""

    target_node_label: str = "TencentCloudVPC"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vpc_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_VPC"
    properties: TencentCloudSubnetToVPCRelProperties = (
        TencentCloudSubnetToVPCRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudSubnetSchema(CartographyNodeSchema):
    """A VPC subnet in one availability zone."""

    label: str = "TencentCloudSubnet"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SUBNET])
    properties: TencentCloudSubnetNodeProperties = TencentCloudSubnetNodeProperties()
    sub_resource_relationship: TencentCloudSubnetToAccountRel = (
        TencentCloudSubnetToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [TencentCloudSubnetToVPCRel()],
    )
