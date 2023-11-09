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
class EC2PrivateIpNetworkInterfaceNodeProperties(CartographyNodeProperties):
    """
    Selection of properties of a private IP as known by an EC2 network interface
    """
    id: PropertyRef = PropertyRef('Id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    network_interface_id: PropertyRef = PropertyRef('NetworkInterfaceId')
    primary: PropertyRef = PropertyRef('Primary')
    private_ip_address: PropertyRef = PropertyRef('PrivateIpAddress')
    public_ip: PropertyRef = PropertyRef('PublicIp')
    ip_owner_id: PropertyRef = PropertyRef('IpOwnerId')


@dataclass(frozen=True)
class EC2PrivateIpToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2PrivateIpToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2PrivateIpToAwsAccountRelProperties = EC2PrivateIpToAwsAccountRelProperties()


@dataclass(frozen=True)
class EC2NetworkInterfaceToPrivateIpRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2PrivateIpToNetworkInterface(CartographyRelSchema):
    target_node_label: str = 'NetworkInterface'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('NetworkInterfaceId')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PRIVATE_IP_ADDRESS"
    properties: EC2NetworkInterfaceToPrivateIpRelProperties = EC2NetworkInterfaceToPrivateIpRelProperties()


@dataclass(frozen=True)
class EC2PrivateIpNetworkInterfaceSchema(CartographyNodeSchema):
    """
    PrivateIp as known by a Network Interface
    """
    label: str = 'EC2PrivateIp'
    properties: EC2PrivateIpNetworkInterfaceNodeProperties = EC2PrivateIpNetworkInterfaceNodeProperties()
    sub_resource_relationship: EC2PrivateIpToAWSAccount = EC2PrivateIpToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2PrivateIpToNetworkInterface(),
        ],
    )
