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
from cartography.models.ontology.labels import COMPUTE_INSTANCE


@dataclass(frozen=True)
class TencentCloudCVMInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Instance ID, e.g. `ins-xxxxxxxx`.")
    uuid: PropertyRef = PropertyRef(
        "uuid", description="Globally unique UUID of the instance."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the instance.")
    hostname: PropertyRef = PropertyRef(
        "hostname", extra_index=True, description="Host name of the instance."
    )
    region: PropertyRef = PropertyRef(
        "region", extra_index=True, description="Region the instance is in."
    )
    zone: PropertyRef = PropertyRef(
        "zone", description="Availability zone the instance is in."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id",
        description="ID of the Tencent Cloud project the instance belongs to.",
    )
    instance_type: PropertyRef = PropertyRef(
        "instance_type", description="Instance model, e.g. `S5.MEDIUM4`."
    )
    cpu: PropertyRef = PropertyRef("cpu", description="Number of vCPUs.")
    memory: PropertyRef = PropertyRef("memory", description="Memory, in GiB.")
    state: PropertyRef = PropertyRef(
        "state",
        description="Instance state, e.g. `RUNNING`, `STOPPED`, `PENDING`, `SHUTDOWN`.",
    )
    restrict_state: PropertyRef = PropertyRef(
        "restrict_state",
        description="Business state: `NORMAL`, `EXPIRED`, or `PROTECTIVELY_ISOLATED`.",
    )
    image_id: PropertyRef = PropertyRef(
        "image_id", description="ID of the image the instance was launched from."
    )
    os_name: PropertyRef = PropertyRef("os_name", description="Operating system name.")
    private_ip_addresses: PropertyRef = PropertyRef(
        "private_ip_addresses",
        description="Private IPv4 addresses of the primary network interface.",
    )
    public_ip_addresses: PropertyRef = PropertyRef(
        "public_ip_addresses",
        description="Public IPv4 addresses of the primary network interface.",
    )
    private_ip_address: PropertyRef = PropertyRef(
        "private_ip_address",
        description="Primary private IPv4 address (first entry of `private_ip_addresses`).",
    )
    public_ip_address: PropertyRef = PropertyRef(
        "public_ip_address",
        description="Primary public IPv4 address (first entry of `public_ip_addresses`), if any.",
    )
    ipv6_addresses: PropertyRef = PropertyRef(
        "ipv6_addresses", description="IPv6 addresses of the instance."
    )
    internet_max_bandwidth_out: PropertyRef = PropertyRef(
        "internet_max_bandwidth_out",
        description="Public outbound bandwidth cap, in Mbps. `0` means no public bandwidth.",
    )
    vpc_id: PropertyRef = PropertyRef(
        "vpc_id", description="ID of the VPC the instance is in."
    )
    subnet_id: PropertyRef = PropertyRef(
        "subnet_id", description="ID of the subnet the instance is in."
    )
    security_group_ids: PropertyRef = PropertyRef(
        "security_group_ids",
        description="IDs of the security groups the instance is in.",
    )
    cam_role_name: PropertyRef = PropertyRef(
        "cam_role_name",
        description="Name of the CAM role bound to the instance. Code on the instance can obtain its credentials.",
    )
    key_ids: PropertyRef = PropertyRef(
        "key_ids", description="IDs of the SSH key pairs bound to the instance."
    )
    disable_api_termination: PropertyRef = PropertyRef(
        "disable_api_termination",
        description="`True` when API termination protection is on.",
    )
    instance_charge_type: PropertyRef = PropertyRef(
        "instance_charge_type",
        description="Billing mode, e.g. `PREPAID`, `POSTPAID_BY_HOUR`.",
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags on the instance, as `key:value` strings."
    )
    created_time: PropertyRef = PropertyRef(
        "created_time", description="Time the instance was created."
    )
    expired_time: PropertyRef = PropertyRef(
        "expired_time", description="Expiry time of a prepaid instance."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TencentCloudCVMInstanceToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudAccount)-[:RESOURCE]->(:TencentCloudCVMInstance)
class TencentCloudCVMInstanceToAccountRel(CartographyRelSchema):
    """Connects a `TencentCloudAccount` to its CVM instances."""

    target_node_label: str = "TencentCloudAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TencentCloudCVMInstanceToAccountRelProperties = (
        TencentCloudCVMInstanceToAccountRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCVMInstanceToVPCRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudCVMInstance)-[:PART_OF_VPC]->(:TencentCloudVPC)
class TencentCloudCVMInstanceToVPCRel(CartographyRelSchema):
    """Connects an instance to its VPC."""

    target_node_label: str = "TencentCloudVPC"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vpc_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_VPC"
    properties: TencentCloudCVMInstanceToVPCRelProperties = (
        TencentCloudCVMInstanceToVPCRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCVMInstanceToSubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudCVMInstance)-[:PART_OF_SUBNET]->(:TencentCloudSubnet)
class TencentCloudCVMInstanceToSubnetRel(CartographyRelSchema):
    """Connects an instance to its subnet."""

    target_node_label: str = "TencentCloudSubnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("subnet_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_SUBNET"
    properties: TencentCloudCVMInstanceToSubnetRelProperties = (
        TencentCloudCVMInstanceToSubnetRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCVMInstanceToSecurityGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudCVMInstance)-[:MEMBER_OF_SECURITY_GROUP]->(:TencentCloudSecurityGroup)
class TencentCloudCVMInstanceToSecurityGroupRel(CartographyRelSchema):
    """Connects an instance to each security group it is in."""

    target_node_label: str = "TencentCloudSecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("security_group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_SECURITY_GROUP"
    properties: TencentCloudCVMInstanceToSecurityGroupRelProperties = (
        TencentCloudCVMInstanceToSecurityGroupRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCVMInstanceToCAMRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TencentCloudCVMInstance)-[:ASSUMES]->(:TencentCloudCAMRole)
class TencentCloudCVMInstanceToCAMRoleRel(CartographyRelSchema):
    """Connects an instance to the CAM role bound to it. Anything running on the instance
    can fetch that role's temporary credentials from the metadata service."""

    target_node_label: str = "TencentCloudCAMRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("cam_role_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMES"
    properties: TencentCloudCVMInstanceToCAMRoleRelProperties = (
        TencentCloudCVMInstanceToCAMRoleRelProperties()
    )


@dataclass(frozen=True)
class TencentCloudCVMInstanceSchema(CartographyNodeSchema):
    """A Cloud Virtual Machine (CVM) instance."""

    label: str = "TencentCloudCVMInstance"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_INSTANCE])
    properties: TencentCloudCVMInstanceNodeProperties = (
        TencentCloudCVMInstanceNodeProperties()
    )
    sub_resource_relationship: TencentCloudCVMInstanceToAccountRel = (
        TencentCloudCVMInstanceToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TencentCloudCVMInstanceToVPCRel(),
            TencentCloudCVMInstanceToSubnetRel(),
            TencentCloudCVMInstanceToSecurityGroupRel(),
            TencentCloudCVMInstanceToCAMRoleRel(),
        ],
    )
