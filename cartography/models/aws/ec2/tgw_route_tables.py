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


# =============================================================================
# Shared rel properties
# =============================================================================


@dataclass(frozen=True)
class TGWRouteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# =============================================================================
# AWSTransitGatewayRouteTable
# =============================================================================


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("TransitGatewayRouteTableId")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    transit_gateway_id: PropertyRef = PropertyRef("TransitGatewayId")
    state: PropertyRef = PropertyRef("State")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableSchema(CartographyNodeSchema):
    label: str = "AWSTransitGatewayRouteTable"
    properties: AWSTransitGatewayRouteTableNodeProperties = (
        AWSTransitGatewayRouteTableNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships([])


# =============================================================================
# AWSTransitGatewayRoute
# =============================================================================


@dataclass(frozen=True)
class AWSTransitGatewayRouteNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    transit_gateway_route_table_id: PropertyRef = PropertyRef("transit_gateway_route_table_id")
    destination_cidr_block: PropertyRef = PropertyRef("destination_cidr_block")
    destination_ipv6_cidr_block: PropertyRef = PropertyRef("destination_ipv6_cidr_block")
    target: PropertyRef = PropertyRef("_target")
    state: PropertyRef = PropertyRef("state")
    origin: PropertyRef = PropertyRef("origin")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSTransitGatewayRouteToAWSAccountRelRelProperties = (
        AWSTransitGatewayRouteToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class AWSTransitGatewayRouteToAttachmentRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteToAttachmentRel(CartographyRelSchema):
    target_node_label: str = "AWSTransitGatewayAttachment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("target")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO_TGW_ATTACHMENT"
    properties: AWSTransitGatewayRouteToAttachmentRelRelProperties = (
        AWSTransitGatewayRouteToAttachmentRelRelProperties()
    )


@dataclass(frozen=True)
class AWSTransitGatewayRouteToTGWRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteToTGWRel(CartographyRelSchema):
    target_node_label: str = "AWSTransitGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"tgw_id": PropertyRef("transit_gateway_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ROUTES_TO_TGW"
    properties: AWSTransitGatewayRouteToTGWRelRelProperties = (
        AWSTransitGatewayRouteToTGWRelRelProperties()
    )


@dataclass(frozen=True)
class AWSTransitGatewayRouteSchema(CartographyNodeSchema):
    label: str = "AWSTransitGatewayRoute"
    properties: AWSTransitGatewayRouteNodeProperties = (
        AWSTransitGatewayRouteNodeProperties()
    )
    sub_resource_relationship: AWSTransitGatewayRouteToAWSAccountRel = (
        AWSTransitGatewayRouteToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSTransitGatewayRouteToAttachmentRel(),
            AWSTransitGatewayRouteToTGWRel(),
        ]
    )


# =============================================================================
# AWSTransitGatewayRouteTableAssociation
# =============================================================================


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableAssociationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    route_table_id: PropertyRef = PropertyRef("route_table_id")
    attachment_id: PropertyRef = PropertyRef("attachment_id")
    resource_id: PropertyRef = PropertyRef("resource_id")
    resource_type: PropertyRef = PropertyRef("resource_type")
    state: PropertyRef = PropertyRef("state")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableAssociationToRouteTableRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableAssociationToRouteTableRel(CartographyRelSchema):
    target_node_label: str = "AWSTransitGatewayRouteTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("route_table_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSTransitGatewayRouteTableAssociationToRouteTableRelRelProperties = (
        AWSTransitGatewayRouteTableAssociationToRouteTableRelRelProperties()
    )


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableAssociationSchema(CartographyNodeSchema):
    label: str = "AWSTransitGatewayRouteTableAssociation"
    properties: AWSTransitGatewayRouteTableAssociationNodeProperties = (
        AWSTransitGatewayRouteTableAssociationNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships([
        AWSTransitGatewayRouteTableAssociationToRouteTableRel(),
    ])


# =============================================================================
# AWSTransitGatewayRouteTablePropagation
# =============================================================================


@dataclass(frozen=True)
class AWSTransitGatewayRouteTablePropagationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    route_table_id: PropertyRef = PropertyRef("route_table_id")
    attachment_id: PropertyRef = PropertyRef("attachment_id")
    state: PropertyRef = PropertyRef("state")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteTablePropagationToRouteTableRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteTablePropagationToRouteTableRel(CartographyRelSchema):
    target_node_label: str = "AWSTransitGatewayRouteTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("route_table_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PROPAGATED_BY"
    properties: AWSTransitGatewayRouteTablePropagationToRouteTableRelRelProperties = (
        AWSTransitGatewayRouteTablePropagationToRouteTableRelRelProperties()
    )


@dataclass(frozen=True)
class AWSTransitGatewayRouteTablePropagationSchema(CartographyNodeSchema):
    label: str = "AWSTransitGatewayRouteTablePropagation"
    properties: AWSTransitGatewayRouteTablePropagationNodeProperties = (
        AWSTransitGatewayRouteTablePropagationNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships([
        AWSTransitGatewayRouteTablePropagationToRouteTableRel(),
    ])
