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
class EC2NetworkInterfaceInstanceNodeProperties(CartographyNodeProperties):
    """
    Selection of properties of a network interface as known by an EC2 instance
    """

    # arn: PropertyRef = PropertyRef('Arn', extra_index=True) TODO use arn; issue #1024
    id: PropertyRef = PropertyRef(
        "NetworkInterfaceId",
        description="The ID of the network interface.  (known as `networkInterfaceId` in EC2)",
    )
    status: PropertyRef = PropertyRef(
        "Status",
        description="Status of the network interface.  Valid Values: ``available \\",
    )
    mac_address: PropertyRef = PropertyRef(
        "MacAddress",
        extra_index=True,
        description="The MAC address of the network interface",
    )
    description: PropertyRef = PropertyRef(
        "Description", description="Description of the network interface"
    )
    private_dns_name: PropertyRef = PropertyRef(
        "PrivateDnsName", extra_index=True, description="The private DNS name"
    )
    private_ip_address: PropertyRef = PropertyRef(
        "PrivateIpAddress",
        extra_index=True,
        description="The primary IPv4 address of the network interface within the subnet",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class EC2NetworkInterfaceToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkInterfaceToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSNetworkInterface`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2NetworkInterfaceToAWSAccountRelProperties = (
        EC2NetworkInterfaceToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class EC2NetworkInterfaceToEC2InstanceRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkInterfaceToEC2InstanceRel(CartographyRelSchema):
    "Represents a `NETWORK_INTERFACE` relationship from `AWSEC2Instance` to `AWSNetworkInterface`."

    target_node_label: str = "AWSEC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("InstanceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "NETWORK_INTERFACE"
    properties: EC2NetworkInterfaceToEC2InstanceRelRelProperties = (
        EC2NetworkInterfaceToEC2InstanceRelRelProperties()
    )


@dataclass(frozen=True)
class EC2NetworkInterfaceToEC2SubnetRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkInterfaceToEC2SubnetRel(CartographyRelSchema):
    "Represents a `PART_OF_SUBNET` relationship from `AWSNetworkInterface` to `AWSEC2Subnet`."

    target_node_label: str = "AWSEC2Subnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SubnetId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_SUBNET"
    properties: EC2NetworkInterfaceToEC2SubnetRelRelProperties = (
        EC2NetworkInterfaceToEC2SubnetRelRelProperties()
    )


@dataclass(frozen=True)
class EC2NetworkInterfaceToEC2SecurityGroupRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkInterfaceToEC2SecurityGroupRel(CartographyRelSchema):
    "Represents a `MEMBER_OF_EC2_SECURITY_GROUP` relationship from `AWSNetworkInterface` to `AWSEC2SecurityGroup`."

    target_node_label: str = "AWSEC2SecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("GroupId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
    properties: EC2NetworkInterfaceToEC2SecurityGroupRelRelProperties = (
        EC2NetworkInterfaceToEC2SecurityGroupRelRelProperties()
    )


@dataclass(frozen=True)
class EC2NetworkInterfaceInstanceSchema(CartographyNodeSchema):
    "Represents an Elastic Network Interface (ENI) in Amazon EC2."

    # Implementation note:
    # Network interface as known by an EC2 instance

    label: str = "AWSNetworkInterface"
    # DEPRECATED: legacy NetworkInterface node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["NetworkInterface"])
    properties: EC2NetworkInterfaceInstanceNodeProperties = (
        EC2NetworkInterfaceInstanceNodeProperties()
    )
    sub_resource_relationship: EC2NetworkInterfaceToAWSAccountRel = (
        EC2NetworkInterfaceToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2NetworkInterfaceToEC2InstanceRel(),
            EC2NetworkInterfaceToEC2SubnetRel(),
            EC2NetworkInterfaceToEC2SecurityGroupRel(),
        ],
    )
