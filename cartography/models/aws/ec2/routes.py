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
class RouteNodeProperties(CartographyNodeProperties):
    """
    Schema describing a Route.
    """
    id: PropertyRef = PropertyRef('RouteId')
    route_id: PropertyRef = PropertyRef('RouteId', extra_index=True)
    carrier_gateway_id: PropertyRef = PropertyRef('CarrierGatewayId')
    core_network_arn: PropertyRef = PropertyRef('CoreNetworkArn')
    destination_cidr_block: PropertyRef = PropertyRef('DestinationCidrBlock')
    destination_ipv6_cidr_block: PropertyRef = PropertyRef('DestinationIpv6CidrBlock')
    destination_prefix_list_id: PropertyRef = PropertyRef('DestinationPrefixListId')
    egress_only_internet_gateway_id: PropertyRef = PropertyRef('EgressOnlyInternetGatewayId')
    gateway_id: PropertyRef = PropertyRef('GatewayId')
    instance_id: PropertyRef = PropertyRef('InstanceId')
    instance_owner_id: PropertyRef = PropertyRef('InstanceOwnerId')
    local_gateway_id: PropertyRef = PropertyRef('LocalGatewayId')
    nat_gateway_id: PropertyRef = PropertyRef('NatGatewayId')
    network_interface_id: PropertyRef = PropertyRef('NetworkInterfaceId')
    origin: PropertyRef = PropertyRef('Origin')
    state: PropertyRef = PropertyRef('State')
    transit_gateway_id: PropertyRef = PropertyRef('TransitGatewayId')
    vpc_peering_connection_id: PropertyRef = PropertyRef('VpcPeeringConnectionId')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class RouteToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class RouteToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RouteToAwsAccountRelProperties = RouteToAwsAccountRelProperties()


@dataclass(frozen=True)
class RouteSchema(CartographyNodeSchema):
    label: str = 'EC2Route'
    properties: RouteNodeProperties = RouteNodeProperties()
    sub_resource_relationship: RouteToAWSAccount = RouteToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships([])
