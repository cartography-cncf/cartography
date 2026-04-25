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
class AWSNatGatewayNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("NatGatewayId")
    nat_gateway_id: PropertyRef = PropertyRef("NatGatewayId", extra_index=True)
    subnet_id: PropertyRef = PropertyRef("SubnetId")
    vpc_id: PropertyRef = PropertyRef("VpcId")
    state: PropertyRef = PropertyRef("State")
    create_time: PropertyRef = PropertyRef("CreateTime")
    allocation_id: PropertyRef = PropertyRef("AllocationId")
    allocation_ids: PropertyRef = PropertyRef("AllocationIds")
    network_interface_id: PropertyRef = PropertyRef("NetworkInterfaceId")
    private_ip: PropertyRef = PropertyRef("PrivateIp")
    public_ip: PropertyRef = PropertyRef("PublicIp")
    connectivity_type: PropertyRef = PropertyRef("ConnectivityType")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSNatGatewayToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSNatGatewayToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSNatGatewayToAWSAccountRelProperties = (
        AWSNatGatewayToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSNatGatewayToAWSVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSNatGatewayToAWSVpcRel(CartographyRelSchema):
    target_node_label: str = "AWSVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VpcId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: AWSNatGatewayToAWSVpcRelProperties = (
        AWSNatGatewayToAWSVpcRelProperties()
    )


@dataclass(frozen=True)
class AWSNatGatewayToEC2SubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSNatGatewayToEC2SubnetRel(CartographyRelSchema):
    target_node_label: str = "EC2Subnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SubnetId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_SUBNET"
    properties: AWSNatGatewayToEC2SubnetRelProperties = (
        AWSNatGatewayToEC2SubnetRelProperties()
    )


@dataclass(frozen=True)
class AWSNatGatewayToElasticIPRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSNatGatewayToElasticIPRel(CartographyRelSchema):
    target_node_label: str = "ElasticIPAddress"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"allocation_id": PropertyRef("AllocationIds", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: AWSNatGatewayToElasticIPRelProperties = (
        AWSNatGatewayToElasticIPRelProperties()
    )


@dataclass(frozen=True)
class AWSNatGatewaySchema(CartographyNodeSchema):
    label: str = "AWSNatGateway"
    properties: AWSNatGatewayNodeProperties = AWSNatGatewayNodeProperties()
    sub_resource_relationship: AWSNatGatewayToAWSAccountRel = (
        AWSNatGatewayToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSNatGatewayToAWSVpcRel(),
            AWSNatGatewayToEC2SubnetRel(),
            AWSNatGatewayToElasticIPRel(),
        ],
    )
