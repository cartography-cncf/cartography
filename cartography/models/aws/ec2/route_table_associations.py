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
    id: PropertyRef = PropertyRef("id")
    route_table_association_id: PropertyRef = PropertyRef("id", extra_index=True)
    target: PropertyRef = PropertyRef("_target")
    gateway_id: PropertyRef = PropertyRef("gateway_id")
    main: PropertyRef = PropertyRef("main")
    route_table_id: PropertyRef = PropertyRef("route_table_id")
    subnet_id: PropertyRef = PropertyRef("subnet_id")
    association_state: PropertyRef = PropertyRef("association_state")
    association_state_message: PropertyRef = PropertyRef("association_state_message")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableAssociationToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableAssociationToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RouteTableAssociationToAWSAccountRelRelProperties = (
        RouteTableAssociationToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class RouteTableAssociationToSubnetRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableAssociationToSubnetRel(CartographyRelSchema):
    target_node_label: str = "EC2Subnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"subnetid": PropertyRef("subnet_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_SUBNET"
    properties: RouteTableAssociationToSubnetRelRelProperties = (
        RouteTableAssociationToSubnetRelRelProperties()
    )


@dataclass(frozen=True)
class RouteTableAssociationToIgwRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RouteTableAssociationToIgwRel(CartographyRelSchema):
    target_node_label: str = "AWSInternetGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gateway_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_IGW_FOR_INGRESS"
    properties: RouteTableAssociationToIgwRelRelProperties = (
        RouteTableAssociationToIgwRelRelProperties()
    )


@dataclass(frozen=True)
class RouteTableAssociationSchema(CartographyNodeSchema):
    label: str = "EC2RouteTableAssociation"
    properties: RouteTableAssociationNodeProperties = (
        RouteTableAssociationNodeProperties()
    )
    sub_resource_relationship: RouteTableAssociationToAWSAccountRel = (
        RouteTableAssociationToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RouteTableAssociationToSubnetRel(),
            RouteTableAssociationToIgwRel(),
        ],
    )
