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
class RouteTableNodeProperties(CartographyNodeProperties):
    """
    Schema describing a RouteTable.
    """
    id: PropertyRef = PropertyRef('RouteTableId')
    route_table_id: PropertyRef = PropertyRef('RouteTableId', extra_index=True)
    associations: PropertyRef = PropertyRef('Associations')
    owner_id: PropertyRef = PropertyRef('OwnerId')
    propagating_vgws: PropertyRef = PropertyRef('PropagatingVgws')
    routes: PropertyRef = PropertyRef('Routes')
    tags: PropertyRef = PropertyRef('Tags')
    vpc_id: PropertyRef = PropertyRef('VpcId')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RouteTableToAwsAccountRelProperties = RouteTableToAwsAccountRelProperties()


@dataclass(frozen=True)
class RouteTableToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableToVpc(CartographyRelSchema):
    target_node_label: str = 'AWSVpc'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('VpcId')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_VPC"
    properties: RouteTableToVpcRelProperties = RouteTableToVpcRelProperties()


@dataclass(frozen=True)
class RouteTableToRouteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableToRoute(CartographyRelSchema):
    target_node_label: str = 'EC2Route'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('RouteId', one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS"
    properties: RouteTableToRouteRelProperties = RouteTableToRouteRelProperties()


@dataclass(frozen=True)
class RouteTableSchema(CartographyNodeSchema):
    label: str = 'EC2RouteTable'
    properties: RouteTableNodeProperties = RouteTableNodeProperties()
    sub_resource_relationship: RouteTableToAWSAccount = RouteTableToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RouteTableToVpc(),
            RouteTableToRoute(),
        ],
    ) 