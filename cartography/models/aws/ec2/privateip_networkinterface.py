from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_EC2_PRIVATE_IP
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
class EC2PrivateIpNetworkInterfaceNodeProperties(CartographyNodeProperties):
    """
    Selection of properties of a private IP as known by an EC2 network interface
    """

    id: PropertyRef = PropertyRef(
        "Id", description="Unique identifier for the private IP"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    network_interface_id: PropertyRef = PropertyRef(
        "NetworkInterfaceId",
        description="id of the network interface with which the IP is associated with",
    )
    primary: PropertyRef = PropertyRef(
        "Primary",
        description="Indicates whether this IPv4 address is the primary private IP address of the network interface.",
    )
    private_ip_address: PropertyRef = PropertyRef(
        "PrivateIpAddress",
        description="The private IPv4 address of the network interface.",
    )
    public_ip: PropertyRef = PropertyRef(
        "PublicIp",
        description="The public IP address or Elastic IP address bound to the network interface.",
    )
    ip_owner_id: PropertyRef = PropertyRef(
        "IpOwnerId", description="Id of the owner, e.g. `amazon-elb` for ELBs"
    )


@dataclass(frozen=True)
class EC2PrivateIpToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2PrivateIpToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2PrivateIpToAWSAccountRelRelProperties = (
        EC2PrivateIpToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class EC2NetworkInterfaceToPrivateIpRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2PrivateIpToNetworkInterfaceRel(CartographyRelSchema):
    target_node_label: str = "AWSNetworkInterface"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NetworkInterfaceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PRIVATE_IP_ADDRESS"
    properties: EC2NetworkInterfaceToPrivateIpRelProperties = (
        EC2NetworkInterfaceToPrivateIpRelProperties()
    )


@dataclass(frozen=True)
class EC2PrivateIpNetworkInterfaceSchema(CartographyNodeSchema):
    """Representation of an AWS EC2 [InstancePrivateIpAddress](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstancePrivateIpAddress.html)"""

    label: str = "AWSEC2PrivateIp"
    # DEPRECATED: legacy EC2PrivateIp node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LEGACY_EC2_PRIVATE_IP])
    properties: EC2PrivateIpNetworkInterfaceNodeProperties = (
        EC2PrivateIpNetworkInterfaceNodeProperties()
    )
    sub_resource_relationship: EC2PrivateIpToAWSAccountRel = (
        EC2PrivateIpToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2PrivateIpToNetworkInterfaceRel(),
        ],
    )
