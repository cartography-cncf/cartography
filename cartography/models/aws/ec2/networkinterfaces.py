from dataclasses import dataclass

from cartography.models.aws.ec2.networkinterface_instance import (
    EC2NetworkInterfaceToAWSAccountRel,
)
from cartography.models.aws.ec2.networkinterface_instance import (
    EC2NetworkInterfaceToEC2InstanceRel,
)
from cartography.models.aws.ec2.networkinterface_instance import (
    EC2NetworkInterfaceToEC2SecurityGroupRel,
)
from cartography.models.aws.ec2.networkinterface_instance import (
    EC2NetworkInterfaceToEC2SubnetRel,
)
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
class EC2NetworkInterfaceNodeProperties(CartographyNodeProperties):
    """
    Network interface properties
    """

    id: PropertyRef = PropertyRef(
        "NetworkInterfaceId",
        description="The ID of the network interface.  (known as `networkInterfaceId` in EC2)",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    description: PropertyRef = PropertyRef(
        "Description", description="Description of the network interface"
    )
    mac_address: PropertyRef = PropertyRef(
        "MacAddress",
        extra_index=True,
        description="The MAC address of the network interface",
    )
    private_dns_name: PropertyRef = PropertyRef(
        "PrivateDnsName", description="The private DNS name"
    )
    private_ip_address: PropertyRef = PropertyRef(
        "PrivateIpAddress",
        extra_index=True,
        description="The primary IPv4 address of the network interface within the subnet",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region"
    )
    status: PropertyRef = PropertyRef(
        "Status",
        description="Status of the network interface.  Valid Values: ``available \\",
    )

    # Properties only returned by describe-network-interfaces
    interface_type: PropertyRef = PropertyRef(
        "InterfaceType",
        description="Describes the type of network interface. Valid values: `` interface \\",
    )
    public_ip: PropertyRef = PropertyRef(
        "PublicIp",
        extra_index=True,
        description="Public IPv4 address attached to the interface",
    )
    requester_id: PropertyRef = PropertyRef(
        "RequesterId",
        extra_index=True,
        description="Id of the requester, e.g. `amazon-elb` for ELBs",
    )
    requester_managed: PropertyRef = PropertyRef(
        "RequesterManaged",
        description="Indicates whether the interface is managed by the requester",
    )
    source_dest_check: PropertyRef = PropertyRef(
        "SourceDestCheck",
        description="Indicates whether to validate network traffic to or from this network interface.",
    )
    # TODO: remove subnetid once we have migrated to subnet_id
    subnetid: PropertyRef = PropertyRef(
        "SubnetId", extra_index=True, description="The ID of the subnet"
    )
    subnet_id: PropertyRef = PropertyRef(
        "SubnetId", extra_index=True, description="The ID of the subnet"
    )
    attach_time: PropertyRef = PropertyRef(
        "AttachTime",
        description="The timestamp when the network interface was attached to an EC2 instance. For primary interfaces (device_index=0), this reveals the first launch time of the instance [according to AWS](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_Instance.html).",
    )
    device_index: PropertyRef = PropertyRef(
        "DeviceIndex",
        description="The index of the device on the instance for the network interface attachment. A value of `0` indicates the primary (eth0) network interface, which is created when the instance is launched.",
    )


@dataclass(frozen=True)
class EC2NetworkInterfaceToElbRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkInterfaceToElbRel(CartographyRelSchema):
    "Represents a `NETWORK_INTERFACE` relationship from `AWSLoadBalancer` to `AWSNetworkInterface`."

    target_node_label: str = "AWSLoadBalancer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("ElbV1Id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "NETWORK_INTERFACE"
    properties: EC2NetworkInterfaceToElbRelRelProperties = (
        EC2NetworkInterfaceToElbRelRelProperties()
    )


@dataclass(frozen=True)
class EC2NetworkInterfaceToElbV2RelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkInterfaceToElbV2Rel(CartographyRelSchema):
    "Represents a `NETWORK_INTERFACE` relationship from `AWSLoadBalancerV2` to `AWSNetworkInterface`."

    target_node_label: str = "AWSLoadBalancerV2"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ElbV2Id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "NETWORK_INTERFACE"
    properties: EC2NetworkInterfaceToElbV2RelRelProperties = (
        EC2NetworkInterfaceToElbV2RelRelProperties()
    )


@dataclass(frozen=True)
class EC2NetworkInterfaceSchema(CartographyNodeSchema):
    "Represents an Elastic Network Interface (ENI) in Amazon EC2."

    # Implementation note:
    # Network interface as known by describe-network-interfaces.

    label: str = "AWSNetworkInterface"
    # DEPRECATED: legacy NetworkInterface node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["NetworkInterface"])
    properties: EC2NetworkInterfaceNodeProperties = EC2NetworkInterfaceNodeProperties()
    sub_resource_relationship: EC2NetworkInterfaceToAWSAccountRel = (
        EC2NetworkInterfaceToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2NetworkInterfaceToEC2SubnetRel(),
            EC2NetworkInterfaceToEC2SecurityGroupRel(),
            EC2NetworkInterfaceToElbRel(),
            EC2NetworkInterfaceToElbV2Rel(),
            EC2NetworkInterfaceToEC2InstanceRel(),
        ],
    )
