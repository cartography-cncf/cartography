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
from cartography.models.ontology.labels import LOAD_BALANCER


@dataclass(frozen=True)
class TencentCloudCLBLoadBalancerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Load balancer ID, e.g. `lb-xxxxxxxx`."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the load balancer.")
    region: PropertyRef = PropertyRef(
        "region", extra_index=True, description="Region the load balancer is in."
    )
    load_balancer_type: PropertyRef = PropertyRef(
        "load_balancer_type",
        extra_index=True,
        description="`OPEN` for a public (internet-facing) load balancer, `INTERNAL` for a private one.",
    )
    forward: PropertyRef = PropertyRef(
        "forward", description="`1` for a standard CLB, `0` for a classic CLB."
    )
    domain: PropertyRef = PropertyRef(
        "domain",
        extra_index=True,
        description="Domain name Tencent Cloud assigned to the load balancer.",
    )
    vips: PropertyRef = PropertyRef(
        "vips", description="Virtual IP addresses of the load balancer."
    )
    ip_address: PropertyRef = PropertyRef(
        "ip_address",
        description="Primary virtual IP address (first entry of `vips`).",
    )
    address_ipv6: PropertyRef = PropertyRef(
        "address_ipv6", description="IPv6 address of the load balancer."
    )
    address_ip_version: PropertyRef = PropertyRef(
        "address_ip_version", description="`ipv4` or `ipv6`."
    )
    status: PropertyRef = PropertyRef(
        "status", description="`0` while creating, `1` when running."
    )
    isolation: PropertyRef = PropertyRef(
        "isolation", description="`1` when the load balancer has been isolated."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id",
        description="ID of the Tencent Cloud project the load balancer belongs to.",
    )
    vpc_id: PropertyRef = PropertyRef(
        "vpc_id", description="ID of the VPC the load balancer is in."
    )
    subnet_id: PropertyRef = PropertyRef(
        "subnet_id", description="ID of the subnet of a private load balancer."
    )
    security_group_ids: PropertyRef = PropertyRef(
        "security_group_ids",
        description="IDs of the security groups bound to the load balancer.",
    )
    master_zone: PropertyRef = PropertyRef(
        "master_zone", description="Primary availability zone."
    )
    charge_type: PropertyRef = PropertyRef(
        "charge_type", description="Billing mode, e.g. `PREPAID`, `POSTPAID_BY_HOUR`."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags on the load balancer, as `key:value` strings."
    )
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Time the load balancer was created."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TencentCloudCLBLoadBalancerToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudAccount)-[:RESOURCE]->(:TencentCloudCLBLoadBalancer)
class TencentCloudCLBLoadBalancerToAccountRel(CartographyRelSchema):
    """Connects a `TencentCloudAccount` to its load balancers."""

    target_node_label: str = "TencentCloudAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TencentCloudCLBLoadBalancerToAccountRelProperties = (
        TencentCloudCLBLoadBalancerToAccountRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCLBLoadBalancerToVPCRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudCLBLoadBalancer)-[:PART_OF_VPC]->(:TencentCloudVPC)
class TencentCloudCLBLoadBalancerToVPCRel(CartographyRelSchema):
    """Connects a load balancer to its VPC."""

    target_node_label: str = "TencentCloudVPC"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vpc_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_VPC"
    properties: TencentCloudCLBLoadBalancerToVPCRelProperties = (
        TencentCloudCLBLoadBalancerToVPCRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCLBLoadBalancerToSubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudCLBLoadBalancer)-[:PART_OF_SUBNET]->(:TencentCloudSubnet)
class TencentCloudCLBLoadBalancerToSubnetRel(CartographyRelSchema):
    """Connects a private load balancer to its subnet."""

    target_node_label: str = "TencentCloudSubnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("subnet_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_SUBNET"
    properties: TencentCloudCLBLoadBalancerToSubnetRelProperties = (
        TencentCloudCLBLoadBalancerToSubnetRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCLBLoadBalancerToSecurityGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudCLBLoadBalancer)-[:MEMBER_OF_SECURITY_GROUP]->(:TencentCloudSecurityGroup)
class TencentCloudCLBLoadBalancerToSecurityGroupRel(CartographyRelSchema):
    """Connects a load balancer to each security group bound to it."""

    target_node_label: str = "TencentCloudSecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("security_group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_SECURITY_GROUP"
    properties: TencentCloudCLBLoadBalancerToSecurityGroupRelProperties = (
        TencentCloudCLBLoadBalancerToSecurityGroupRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCLBLoadBalancerToCVMInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudCLBLoadBalancer)-[:EXPOSE]->(:TencentCloudCVMInstance)
class TencentCloudCLBLoadBalancerToCVMInstanceRel(CartographyRelSchema):
    """Connects a load balancer to each CVM instance registered as a backend of one of
    its listeners."""

    target_node_label: str = "TencentCloudCVMInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("backend_instance_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXPOSE"
    properties: TencentCloudCLBLoadBalancerToCVMInstanceRelProperties = (
        TencentCloudCLBLoadBalancerToCVMInstanceRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCLBLoadBalancerSchema(CartographyNodeSchema):
    """A Cloud Load Balancer (CLB) instance."""

    label: str = "TencentCloudCLBLoadBalancer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LOAD_BALANCER])
    properties: TencentCloudCLBLoadBalancerNodeProperties = (
        TencentCloudCLBLoadBalancerNodeProperties()
    )
    sub_resource_relationship: TencentCloudCLBLoadBalancerToAccountRel = (
        TencentCloudCLBLoadBalancerToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TencentCloudCLBLoadBalancerToVPCRel(),
            TencentCloudCLBLoadBalancerToSubnetRel(),
            TencentCloudCLBLoadBalancerToSecurityGroupRel(),
            TencentCloudCLBLoadBalancerToCVMInstanceRel(),
        ],
    )
