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
    id: PropertyRef = PropertyRef('id')
    route_table_id: PropertyRef = PropertyRef('route_table_id', extra_index=True)
    owner_id: PropertyRef = PropertyRef('owner_id')
    vpc_id: PropertyRef = PropertyRef('VpcId')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    main: PropertyRef = PropertyRef('main')


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
        {'id': PropertyRef('vpc_id')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_AWS_VPC"
    properties: RouteTableToVpcRelProperties = RouteTableToVpcRelProperties()


@dataclass(frozen=True)
class RouteTableToRouteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableToRoute(CartographyRelSchema):
    target_node_label: str = 'EC2Route'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('RouteIds', one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTE"
    properties: RouteTableToRouteRelProperties = RouteTableToRouteRelProperties()


@dataclass(frozen=True)
class RouteTableToAssociationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableToAssociation(CartographyRelSchema):
    target_node_label: str = 'EC2RouteTableAssociation'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('RouteTableAssociationIds', one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATION"
    properties: RouteTableToAssociationRelProperties = RouteTableToAssociationRelProperties()


@dataclass(frozen=True)
class RouteTableToVpnGatewayRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


# TODO implement AWSVpnGateways
@dataclass(frozen=True)
class RouteTableToVpnGateway(CartographyRelSchema):
    target_node_label: str = 'AWSVpnGateway'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('VpnGatewayIds', one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTED_TO"
    properties: RouteTableToVpnGatewayRelProperties = RouteTableToVpnGatewayRelProperties()


@dataclass(frozen=True)
class RouteTableSchema(CartographyNodeSchema):
    label: str = 'EC2RouteTable'
    properties: RouteTableNodeProperties = RouteTableNodeProperties()
    sub_resource_relationship: RouteTableToAWSAccount = RouteTableToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RouteTableToVpc(),
            RouteTableToRoute(),
            RouteTableToAssociation(),
            RouteTableToVpnGateway(),
        ],
    )
