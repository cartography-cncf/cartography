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
class AWSRouteTableVPCEndpointNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("RouteTableId")
    route_table_id: PropertyRef = PropertyRef("RouteTableId", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSRouteTableToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSRouteTableToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSRouteTableToAWSAccountRelProperties = (
        AWSRouteTableToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSRouteTableToVPCEndpointRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSRouteTableToVPCEndpointRel(CartographyRelSchema):
    target_node_label: str = "AWSVpcEndpoint"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VpcEndpointId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ROUTES_THROUGH"
    properties: AWSRouteTableToVPCEndpointRelProperties = (
        AWSRouteTableToVPCEndpointRelProperties()
    )


@dataclass(frozen=True)
class AWSRouteTableVPCEndpointSchema(CartographyNodeSchema):
    """
    Route tables as known by describe-vpc-endpoints.
    Creates stub route table nodes and ROUTES_THROUGH relationships from Gateway VPC endpoints.
    """

    label: str = "AWSRouteTable"
    properties: AWSRouteTableVPCEndpointNodeProperties = (
        AWSRouteTableVPCEndpointNodeProperties()
    )
    sub_resource_relationship: AWSRouteTableToAWSAccountRel = (
        AWSRouteTableToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSRouteTableToVPCEndpointRel(),
        ],
    )
