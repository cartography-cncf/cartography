from dataclasses import dataclass

from cartography.models.aws.ec2.subnet_instance import EC2SubnetToAWSAccount
from cartography.models.aws.ec2.subnet_instance import EC2SubnetToEC2Instance
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
class EC2SubnetNetworkInterfaceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('SubnetId')
    subnet_id: PropertyRef = PropertyRef('SubnetId', extra_index=True)
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToNetworkInterfaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToNetworkInterface(CartographyRelSchema):
    target_node_label: str = 'NetworkInterface'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('NetworkInterfaceId')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PART_OF_SUBNET"
    properties: EC2SubnetToNetworkInterfaceRelProperties = EC2SubnetToNetworkInterfaceRelProperties()


@dataclass(frozen=True)
class EC2SubnetToLoadBalancerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToLoadBalancer(CartographyRelSchema):
    target_node_label: str = 'LoadBalancer'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('ElbV1Id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PART_OF_SUBNET"
    properties: EC2SubnetToLoadBalancerRelProperties = EC2SubnetToLoadBalancerRelProperties()


@dataclass(frozen=True)
class EC2SubnetToLoadBalancerV2RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToLoadBalancerV2(CartographyRelSchema):
    target_node_label: str = 'LoadBalancerV2'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('ElbV2Id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PART_OF_SUBNET"
    properties: EC2SubnetToLoadBalancerV2RelProperties = EC2SubnetToLoadBalancerV2RelProperties()


@dataclass(frozen=True)
class EC2SubnetNetworkInterfaceSchema(CartographyNodeSchema):
    """
    Subnet as known by describe-network-interfaces
    """
    label: str = 'EC2Subnet'
    properties: EC2SubnetNetworkInterfaceNodeProperties = EC2SubnetNetworkInterfaceNodeProperties()
    sub_resource_relationship: EC2SubnetToAWSAccount = EC2SubnetToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2SubnetToNetworkInterface(),
            EC2SubnetToEC2Instance(),
            EC2SubnetToLoadBalancer(),
            EC2SubnetToLoadBalancerV2(),
        ],
    )
