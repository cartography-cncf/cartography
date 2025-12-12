from dataclasses import dataclass

from cartography.models.aws.ec2.subnet_instance import EC2SubnetToAWSAccountRel
from cartography.models.aws.ec2.subnet_instance import EC2SubnetToEC2InstanceRel
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
    id: PropertyRef = PropertyRef("SubnetId")
    # TODO: remove subnetid once we have migrated to subnet_id
    subnetid: PropertyRef = PropertyRef("SubnetId", extra_index=True)
    subnet_id: PropertyRef = PropertyRef("SubnetId", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToNetworkInterfaceRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToNetworkInterfaceRel(CartographyRelSchema):
    target_node_label: str = "NetworkInterface"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NetworkInterfaceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PART_OF_SUBNET"
    properties: EC2SubnetToNetworkInterfaceRelRelProperties = (
        EC2SubnetToNetworkInterfaceRelRelProperties()
    )


@dataclass(frozen=True)
class EC2SubnetToLoadBalancerRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToLoadBalancerRel(CartographyRelSchema):
    target_node_label: str = "LoadBalancer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ElbV1Id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PART_OF_SUBNET"
    properties: EC2SubnetToLoadBalancerRelRelProperties = (
        EC2SubnetToLoadBalancerRelRelProperties()
    )


@dataclass(frozen=True)
class EC2SubnetToLoadBalancerV2RelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EC2SubnetToLoadBalancerV2Rel(CartographyRelSchema):
    target_node_label: str = "LoadBalancerV2"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ElbV2Id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PART_OF_SUBNET"
    properties: EC2SubnetToLoadBalancerV2RelRelProperties = (
        EC2SubnetToLoadBalancerV2RelRelProperties()
    )


@dataclass(frozen=True)
class EC2SubnetNetworkInterfaceSchema(CartographyNodeSchema):
    """
    Subnet as known by describe-network-interfaces
    """

    label: str = "EC2Subnet"
    properties: EC2SubnetNetworkInterfaceNodeProperties = (
        EC2SubnetNetworkInterfaceNodeProperties()
    )
    sub_resource_relationship: EC2SubnetToAWSAccountRel = EC2SubnetToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            EC2SubnetToNetworkInterfaceRel(),
            EC2SubnetToEC2InstanceRel(),
            EC2SubnetToLoadBalancerRel(),
            EC2SubnetToLoadBalancerV2Rel(),
        ],
    )
