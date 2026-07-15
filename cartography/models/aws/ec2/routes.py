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
class RouteNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="The ID of the route, formatted as `route_table_id\\"
    )
    carrier_gateway_id: PropertyRef = PropertyRef(
        "carrier_gateway_id", description="The ID of the carrier gateway"
    )
    core_network_arn: PropertyRef = PropertyRef(
        "core_network_arn",
        description="The Amazon Resource Name (ARN) of the core network",
    )
    destination_cidr_block: PropertyRef = PropertyRef(
        "destination_cidr_block",
        description="The IPv4 CIDR block used for the destination match",
    )
    destination_ipv6_cidr_block: PropertyRef = PropertyRef(
        "destination_ipv6_cidr_block",
        description="The IPv6 CIDR block used for the destination match",
    )
    destination_prefix_list_id: PropertyRef = PropertyRef(
        "destination_prefix_list_id",
        description="The ID of the prefix list used for the destination match",
    )
    egress_only_internet_gateway_id: PropertyRef = PropertyRef(
        "egress_only_internet_gateway_id",
        description="The ID of the egress-only internet gateway",
    )
    gateway_id: PropertyRef = PropertyRef(
        "gateway_id", description="The ID of the gateway"
    )
    instance_id: PropertyRef = PropertyRef(
        "instance_id", description="The ID of the instance"
    )
    instance_owner_id: PropertyRef = PropertyRef(
        "instance_owner_id", description="The owner ID of the instance"
    )
    local_gateway_id: PropertyRef = PropertyRef(
        "local_gateway_id", description="The ID of the local gateway"
    )
    nat_gateway_id: PropertyRef = PropertyRef(
        "nat_gateway_id", description="The ID of the NAT gateway"
    )
    network_interface_id: PropertyRef = PropertyRef(
        "network_interface_id", description="The ID of the network interface"
    )
    origin: PropertyRef = PropertyRef("origin", description="How the route was created")
    state: PropertyRef = PropertyRef("state", description="The state of the route")
    transit_gateway_id: PropertyRef = PropertyRef(
        "transit_gateway_id", description="The ID of the transit gateway"
    )
    vpc_peering_connection_id: PropertyRef = PropertyRef(
        "vpc_peering_connection_id", description="The ID of the VPC peering connection"
    )
    vpc_endpoint_id: PropertyRef = PropertyRef(
        "vpc_endpoint_id",
        description="Identifier of the VPC endpoint linked to this `AWSEC2Route` node.",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region the route is in"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    target: PropertyRef = PropertyRef(
        "_target",
        description="The ID of the route association's target -- either 'Main', or a subnet ID or a gateway ID. This is an invented field that we created to have an ID because the underlying EC2 route association is a \"union\" data structure of many different possible targets.",
    )


@dataclass(frozen=True)
class RouteToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RouteToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSEC2Route`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RouteToAWSAccountRelRelProperties = RouteToAWSAccountRelRelProperties()


@dataclass(frozen=True)
class RouteToInternetGatewayRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RouteToInternetGatewayRel(CartographyRelSchema):
    "Represents a `ROUTES_TO_GATEWAY` relationship from `AWSEC2Route` to `AWSInternetGateway`."

    target_node_label: str = "AWSInternetGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gateway_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO_GATEWAY"
    properties: RouteToInternetGatewayRelRelProperties = (
        RouteToInternetGatewayRelRelProperties()
    )


@dataclass(frozen=True)
class RouteToVPCEndpointRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RouteToVPCEndpointRel(CartographyRelSchema):
    "Represents a `ROUTES_TO_VPC_ENDPOINT` relationship from `AWSEC2Route` to `AWSVpcEndpoint`."

    target_node_label: str = "AWSVpcEndpoint"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vpc_endpoint_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO_VPC_ENDPOINT"
    properties: RouteToVPCEndpointRelRelProperties = (
        RouteToVPCEndpointRelRelProperties()
    )


@dataclass(frozen=True)
class RouteSchema(CartographyNodeSchema):
    "Represents an `AWSEC2Route` node in the AWS graph."

    label: str = "AWSEC2Route"
    # DEPRECATED: legacy EC2Route node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EC2Route"])
    properties: RouteNodeProperties = RouteNodeProperties()
    sub_resource_relationship: RouteToAWSAccountRel = RouteToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RouteToInternetGatewayRel(),
            RouteToVPCEndpointRel(),
        ]
    )
