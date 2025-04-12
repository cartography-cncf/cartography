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
class RouteTableAssociationNodeProperties(CartographyNodeProperties):
    """
    Schema describing a RouteTableAssociation.
    """
    id: PropertyRef = PropertyRef('RouteTableAssociationId')
    route_table_association_id: PropertyRef = PropertyRef('RouteTableAssociationId', extra_index=True)
    association_state: PropertyRef = PropertyRef('AssociationState')
    gateway_id: PropertyRef = PropertyRef('GatewayId')
    main: PropertyRef = PropertyRef('Main')
    route_table_id: PropertyRef = PropertyRef('RouteTableId')
    subnet_id: PropertyRef = PropertyRef('SubnetId')
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableAssociationToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableAssociationToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RouteTableAssociationToAwsAccountRelProperties = RouteTableAssociationToAwsAccountRelProperties()


@dataclass(frozen=True)
class RouteTableAssociationToSubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableAssociationToSubnet(CartographyRelSchema):
    target_node_label: str = 'EC2Subnet'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('SubnetId')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: RouteTableAssociationToSubnetRelProperties = RouteTableAssociationToSubnetRelProperties()


@dataclass(frozen=True)
class RouteTableAssociationToGatewayRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableAssociationToGateway(CartographyRelSchema):
    target_node_label: str = 'AWSInternetGateway'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('GatewayId')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: RouteTableAssociationToGatewayRelProperties = RouteTableAssociationToGatewayRelProperties()


@dataclass(frozen=True)
class RouteTableAssociationSchema(CartographyNodeSchema):
    label: str = 'EC2RouteTableAssociation'
    properties: RouteTableAssociationNodeProperties = RouteTableAssociationNodeProperties()
    sub_resource_relationship: RouteTableAssociationToAWSAccount = RouteTableAssociationToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RouteTableAssociationToSubnet(),
            RouteTableAssociationToGateway(),
        ],
    ) 