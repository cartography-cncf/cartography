from dataclasses import dataclass

from cartography.models.aws.ec2.networkinterface_instance import EC2NetworkInterfaceToAWSAccount
from cartography.models.aws.ec2.networkinterface_instance import EC2NetworkInterfaceToEC2Instance
from cartography.models.aws.ec2.networkinterface_instance import EC2NetworkInterfaceToEC2SecurityGroup
from cartography.models.aws.ec2.networkinterface_instance import EC2NetworkInterfaceToEC2Subnet
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
class EC2NetworkInterfaceNodeProperties(CartographyNodeProperties):
    """
    Network interface properties
    """
    id: PropertyRef = PropertyRef('NetworkInterfaceId')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    description: PropertyRef = PropertyRef('Description')
    mac_address: PropertyRef = PropertyRef('MacAddress', extra_index=True)
    private_dns_name: PropertyRef = PropertyRef('PrivateDnsName')
    private_ip_address: PropertyRef = PropertyRef('PrivateIpAddress', extra_index=True)
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    status: PropertyRef = PropertyRef('Status')

    # Properties only returned by describe-network-interfaces
    interface_type: PropertyRef = PropertyRef('InterfaceType')
    public_ip: PropertyRef = PropertyRef('PublicIp', extra_index=True)
    requester_id: PropertyRef = PropertyRef('RequesterId', extra_index=True)
    requester_managed: PropertyRef = PropertyRef('RequesterManaged')
    source_dest_check: PropertyRef = PropertyRef('SourceDestCheck')
    subnetid: PropertyRef = PropertyRef('SubnetId', extra_index=True)


@dataclass(frozen=True)
class EC2NetworkInterfaceToElbRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkInterfaceToElb(CartographyRelSchema):
    target_node_label: str = 'LoadBalancer'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'name': PropertyRef('ElbV1Id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "NETWORK_INTERFACE"
    properties: EC2NetworkInterfaceToElbRelProperties = EC2NetworkInterfaceToElbRelProperties()


@dataclass(frozen=True)
class EC2NetworkInterfaceToElbV2RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2NetworkInterfaceToElbV2(CartographyRelSchema):
    target_node_label: str = 'LoadBalancerV2'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('ElbV2Id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "NETWORK_INTERFACE"
    properties: EC2NetworkInterfaceToElbV2RelProperties = EC2NetworkInterfaceToElbV2RelProperties()


@dataclass(frozen=True)
class EC2NetworkInterfaceSchema(CartographyNodeSchema):
    """
    Network interface as known by describe-network-interfaces.
    """
    label: str = 'NetworkInterface'
    properties: EC2NetworkInterfaceNodeProperties = EC2NetworkInterfaceNodeProperties()
    sub_resource_relationship: EC2NetworkInterfaceToAWSAccount = EC2NetworkInterfaceToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2NetworkInterfaceToEC2Subnet(),
            EC2NetworkInterfaceToEC2SecurityGroup(),
            EC2NetworkInterfaceToElb(),
            EC2NetworkInterfaceToElbV2(),
            EC2NetworkInterfaceToEC2Instance(),
        ],
    )
