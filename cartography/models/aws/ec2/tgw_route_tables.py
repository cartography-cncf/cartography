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
    id: PropertyRef = PropertyRef(
        "TransitGatewayRouteTableId",
        description="Unique identifier of the Transit Gateway Route Table (same as `transit_gateway_route_table_id`)",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    transit_gateway_id: PropertyRef = PropertyRef(
        "TransitGatewayId",
        description="The ID of the Transit Gateway this route table belongs to",
    )
    state: PropertyRef = PropertyRef(
        "State",
        description="Can be one of ``pending | available | deleting | deleted``",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The region of this Transit Gateway Route Table",
    )


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableToTGWRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableToTGWRel(CartographyRelSchema):
    target_node_label: str = "AWSTransitGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"tgw_id": PropertyRef("transit_gateway_id")},
    )
    # INWARD so the edge reads (AWSTransitGateway)-[:CONTAINS]->(RouteTable):
    # active verb, parent->child, per writing-intel-modules.md naming guidelines
    # ("prefer CONTAINS over BELONGS_TO").
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AWSTransitGatewayRouteTableToTGWRelRelProperties = (
        AWSTransitGatewayRouteTableToTGWRelRelProperties()
    )


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSTransitGatewayRouteTableToAWSAccountRelRelProperties = (
        AWSTransitGatewayRouteTableToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableSchema(CartographyNodeSchema):
    """Representation of an [AWS Transit Gateway Route Table](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_TransitGatewayRouteTable.html)."""

    label: str = "AWSTransitGatewayRouteTable"
    properties: AWSTransitGatewayRouteTableNodeProperties = (
        AWSTransitGatewayRouteTableNodeProperties()
    )
    # Links the route table to its owning AWSAccount; required for account-scoped
    # cleanup and so the node is reachable from the account.
    sub_resource_relationship: AWSTransitGatewayRouteTableToAWSAccountRel = (
        AWSTransitGatewayRouteTableToAWSAccountRel()
    )
    # Declared inline (not appended after the class) so the frozen dataclass
    # actually carries the relationship at load time.
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSTransitGatewayRouteTableToTGWRel(),
        ]
    )


# =============================================================================
# AWSTransitGatewayRoute
# =============================================================================


@dataclass(frozen=True)
class AWSTransitGatewayRouteNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Unique identifier of the Transit Gateway Route, of the format "
            "`{transit_gateway_route_table_id}|{destination_cidr_block}`"
        ),
    )
    transit_gateway_route_table_id: PropertyRef = PropertyRef(
        "transit_gateway_route_table_id",
        description="The ID of the Transit Gateway Route Table this route belongs to",
    )
    destination_cidr_block: PropertyRef = PropertyRef(
        "destination_cidr_block",
        description="The IPv4 CIDR block used for destination matches",
    )
    destination_ipv6_cidr_block: PropertyRef = PropertyRef(
        "destination_ipv6_cidr_block",
        description="The IPv6 CIDR block used for destination matches",
    )
    target: PropertyRef = PropertyRef(
        "target",
        description="The ID of the Transit Gateway Attachment this route points to, if any",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Can be one of ``pending | active | blackhole | deleting | deleted``",
    )
    origin: PropertyRef = PropertyRef(
        "origin",
        description=(
            "Currently unpopulated: the underlying `SearchTransitGatewayRoutes` API "
            "returns this as `Type` (``static | propagated``), not `Origin`, so this "
            "field is always null"
        ),
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The region of this Transit Gateway Route",
    )
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


# Route -> RouteTable relationship (model-driven)
@dataclass(frozen=True)
class AWSTransitGatewayRouteToRouteTableRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteToRouteTableRel(CartographyRelSchema):
    target_node_label: str = "AWSTransitGatewayRouteTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("transit_gateway_route_table_id")},
    )
    # INWARD so the edge reads (RouteTable)-[:HAS_ROUTE]->(Route): active verb,
    # parent->child.
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ROUTE"
    properties: AWSTransitGatewayRouteToRouteTableRelRelProperties = (
        AWSTransitGatewayRouteToRouteTableRelRelProperties()
    )


@dataclass(frozen=True)
class AWSTransitGatewayRouteSchema(CartographyNodeSchema):
    """Representation of an [AWS Transit Gateway Route](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_TransitGatewayRoute.html)."""

    label: str = "AWSTransitGatewayRoute"
    properties: AWSTransitGatewayRouteNodeProperties = (
        AWSTransitGatewayRouteNodeProperties()
    )
    sub_resource_relationship: AWSTransitGatewayRouteToAWSAccountRel = (
        AWSTransitGatewayRouteToAWSAccountRel()
    )
    # All relationships declared inline (not appended after the class) so the
    # frozen dataclass carries them at load time.
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSTransitGatewayRouteToAttachmentRel(),
            AWSTransitGatewayRouteToTGWRel(),
            AWSTransitGatewayRouteToRouteTableRel(),
        ]
    )


# =============================================================================
# AWSTransitGatewayRouteTableAssociation
# =============================================================================


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableAssociationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Unique identifier of the association. The API does not return an "
            "association id, so this is synthesized as `{route_table_id}|{attachment_id}`"
        ),
    )
    route_table_id: PropertyRef = PropertyRef(
        "route_table_id",
        description="The ID of the Transit Gateway Route Table this association belongs to",
    )
    attachment_id: PropertyRef = PropertyRef(
        "attachment_id",
        description="The ID of the Transit Gateway Attachment that is associated",
    )
    resource_id: PropertyRef = PropertyRef(
        "resource_id",
        description="The ID of the resource (e.g. VPC) behind the attachment",
    )
    resource_type: PropertyRef = PropertyRef(
        "resource_type",
        description="Can be one of ``vpc | vpn | direct-connect-gateway | tgw-peering``",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description=(
            "Can be one of ``associating | associated | disassociating | disassociated``"
        ),
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The region of this Transit Gateway Route Table Association",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableAssociationToRouteTableRelRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableAssociationToRouteTableRel(CartographyRelSchema):
    target_node_label: str = "AWSTransitGatewayRouteTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("route_table_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: AWSTransitGatewayRouteTableAssociationToRouteTableRelRelProperties = (
        AWSTransitGatewayRouteTableAssociationToRouteTableRelRelProperties()
    )


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableAssociationToAWSAccountRelRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableAssociationToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSTransitGatewayRouteTableAssociationToAWSAccountRelRelProperties = (
        AWSTransitGatewayRouteTableAssociationToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class AWSTransitGatewayRouteTableAssociationSchema(CartographyNodeSchema):
    """Representation of an [AWS Transit Gateway Route Table Association](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_TransitGatewayRouteTableAssociation.html)."""

    label: str = "AWSTransitGatewayRouteTableAssociation"
    properties: AWSTransitGatewayRouteTableAssociationNodeProperties = (
        AWSTransitGatewayRouteTableAssociationNodeProperties()
    )
    sub_resource_relationship: AWSTransitGatewayRouteTableAssociationToAWSAccountRel = (
        AWSTransitGatewayRouteTableAssociationToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSTransitGatewayRouteTableAssociationToRouteTableRel(),
        ]
    )


# =============================================================================
# AWSTransitGatewayRouteTablePropagation
# =============================================================================


@dataclass(frozen=True)
class AWSTransitGatewayRouteTablePropagationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Unique identifier of the propagation. The API does not return a "
            "propagation id, so this is synthesized as `{route_table_id}|{attachment_id}`"
        ),
    )
    route_table_id: PropertyRef = PropertyRef(
        "route_table_id",
        description="The ID of the Transit Gateway Route Table this propagation belongs to",
    )
    attachment_id: PropertyRef = PropertyRef(
        "attachment_id",
        description="The ID of the Transit Gateway Attachment that is propagating routes",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Can be one of ``enabling | enabled | disabling | disabled``",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The region of this Transit Gateway Route Table Propagation",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteTablePropagationToRouteTableRelRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteTablePropagationToRouteTableRel(CartographyRelSchema):
    target_node_label: str = "AWSTransitGatewayRouteTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("route_table_id")},
    )
    # INWARD already yields (RouteTable)-[:PROPAGATES]->(Propagation): active
    # verb, parent->child, replacing the passive *_BY form PROPAGATED_BY.
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "PROPAGATES"
    properties: AWSTransitGatewayRouteTablePropagationToRouteTableRelRelProperties = (
        AWSTransitGatewayRouteTablePropagationToRouteTableRelRelProperties()
    )


@dataclass(frozen=True)
class AWSTransitGatewayRouteTablePropagationToAWSAccountRelRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSTransitGatewayRouteTablePropagationToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSTransitGatewayRouteTablePropagationToAWSAccountRelRelProperties = (
        AWSTransitGatewayRouteTablePropagationToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class AWSTransitGatewayRouteTablePropagationSchema(CartographyNodeSchema):
    """Representation of an [AWS Transit Gateway Route Table Propagation](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_TransitGatewayRouteTablePropagation.html)."""

    label: str = "AWSTransitGatewayRouteTablePropagation"
    properties: AWSTransitGatewayRouteTablePropagationNodeProperties = (
        AWSTransitGatewayRouteTablePropagationNodeProperties()
    )
    sub_resource_relationship: AWSTransitGatewayRouteTablePropagationToAWSAccountRel = (
        AWSTransitGatewayRouteTablePropagationToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSTransitGatewayRouteTablePropagationToRouteTableRel(),
        ]
    )
