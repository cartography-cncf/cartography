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
    id: PropertyRef = PropertyRef("id")
    carrier_gateway_id: PropertyRef = PropertyRef("carrier_gateway_id")
    core_network_arn: PropertyRef = PropertyRef("core_network_arn")
    destination_cidr_block: PropertyRef = PropertyRef("destination_cidr_block")
    destination_ipv6_cidr_block: PropertyRef = PropertyRef(
        "destination_ipv6_cidr_block"
    )
    destination_prefix_list_id: PropertyRef = PropertyRef("destination_prefix_list_id")
    egress_only_internet_gateway_id: PropertyRef = PropertyRef(
        "egress_only_internet_gateway_id"
    )
    gateway_id: PropertyRef = PropertyRef("gateway_id")
    instance_id: PropertyRef = PropertyRef("instance_id")
    instance_owner_id: PropertyRef = PropertyRef("instance_owner_id")
    local_gateway_id: PropertyRef = PropertyRef("local_gateway_id")
    nat_gateway_id: PropertyRef = PropertyRef("nat_gateway_id")
    network_interface_id: PropertyRef = PropertyRef("network_interface_id")
    origin: PropertyRef = PropertyRef("origin")
    state: PropertyRef = PropertyRef("state")
    transit_gateway_id: PropertyRef = PropertyRef("transit_gateway_id")
    vpc_peering_connection_id: PropertyRef = PropertyRef("vpc_peering_connection_id")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    target: PropertyRef = PropertyRef("_target")


@dataclass(frozen=True)
class RouteToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RouteToAWSAccountRel(CartographyRelSchema):
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
class RouteSchema(CartographyNodeSchema):
    label: str = "EC2Route"
    properties: RouteNodeProperties = RouteNodeProperties()
    sub_resource_relationship: RouteToAWSAccountRel = RouteToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RouteToInternetGatewayRel(),
        ]
    )
