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
class DirectConnectGatewayNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "directConnectGatewayId", description="The ID of the Direct Connect gateway"
    )
    name: PropertyRef = PropertyRef(
        "directConnectGatewayName", description="The name of the Direct Connect gateway"
    )
    state: PropertyRef = PropertyRef(
        "directConnectGatewayState",
        description="The state of the gateway. Valid values: pending, available, deleting, deleted",
    )
    owner_account: PropertyRef = PropertyRef(
        "ownerAccount",
        description="The AWS account that owns the Direct Connect gateway",
    )
    amazon_side_asn: PropertyRef = PropertyRef(
        "amazonSideAsn",
        description="The autonomous system number (ASN) of the Amazon side",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The region the gateway was collected from. Direct Connect gateways are global",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DirectConnectGatewayToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DirectConnectGatewayToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DirectConnectGatewayToAWSAccountRelProperties = (
        DirectConnectGatewayToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class DirectConnectGatewaySchema(CartographyNodeSchema):
    """Representation of an AWS [Direct Connect gateway](https://docs.aws.amazon.com/directconnect/latest/APIReference/API_DirectConnectGateway.html): a global object that connects virtual interfaces to VPCs across regions."""

    label: str = "AWSDirectConnectGateway"
    properties: DirectConnectGatewayNodeProperties = (
        DirectConnectGatewayNodeProperties()
    )
    sub_resource_relationship: DirectConnectGatewayToAWSAccountRel = (
        DirectConnectGatewayToAWSAccountRel()
    )


# --- Association: the Direct Connect gateway attached to a VGW or Transit Gateway ---


@dataclass(frozen=True)
class DirectConnectGatewayAssociationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "associationId", description="The ID of the Direct Connect gateway association"
    )
    direct_connect_gateway_id: PropertyRef = PropertyRef(
        "directConnectGatewayId",
        description="The ID of the associated Direct Connect gateway",
    )
    state: PropertyRef = PropertyRef(
        "associationState",
        description="The state of the association. Valid values: associating, associated, disassociating, disassociated, updating",
    )
    associated_gateway_id: PropertyRef = PropertyRef(
        "AssociatedGatewayId",
        extra_index=True,
        description="The ID of the virtual private gateway or transit gateway on the other side",
    )
    associated_gateway_type: PropertyRef = PropertyRef(
        "AssociatedGatewayType",
        description="The type of the associated gateway. Valid values: virtualPrivateGateway, transitGateway",
    )
    associated_gateway_owner: PropertyRef = PropertyRef(
        "AssociatedGatewayOwner",
        description="The AWS account that owns the associated gateway. Differs from the gateway owner on cross-account associations",
    )
    associated_gateway_region: PropertyRef = PropertyRef(
        "AssociatedGatewayRegion", description="The region of the associated gateway"
    )
    allowed_prefixes: PropertyRef = PropertyRef(
        "AllowedPrefixes",
        description=(
            "The CIDR prefixes advertised from the associated gateway to the Direct Connect "
            "gateway, and therefore reachable from the on-premises network over this association"
        ),
    )
    owner_account: PropertyRef = PropertyRef(
        "directConnectGatewayOwnerAccount",
        description="The AWS account that owns the Direct Connect gateway",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The region the association was collected from",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DirectConnectGatewayAssociationToAWSAccountRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DirectConnectGatewayAssociationToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DirectConnectGatewayAssociationToAWSAccountRelProperties = (
        DirectConnectGatewayAssociationToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AssociationToGatewayRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AssociationToGatewayRel(CartographyRelSchema):
    target_node_label: str = "AWSDirectConnectGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("directConnectGatewayId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: AssociationToGatewayRelProperties = AssociationToGatewayRelProperties()


@dataclass(frozen=True)
class AssociationToTransitGatewayRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AssociationToTransitGatewayRel(CartographyRelSchema):
    """
    Links the association to the Transit Gateway on the other side, when there is one. This is
    the edge that completes the path from an on-premises network to a Transit Gateway. Virtual
    private gateway associations record the gateway ID on the node but match no node here.
    """

    target_node_label: str = "AWSTransitGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"tgw_id": PropertyRef("AssociatedGatewayId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: AssociationToTransitGatewayRelProperties = (
        AssociationToTransitGatewayRelProperties()
    )


@dataclass(frozen=True)
class DirectConnectGatewayAssociationSchema(CartographyNodeSchema):
    """Representation of an AWS [Direct Connect gateway association](https://docs.aws.amazon.com/directconnect/latest/APIReference/API_DirectConnectGatewayAssociation.html): the attachment between a Direct Connect gateway and a virtual private gateway or transit gateway, carrying the prefixes advertised over it."""

    label: str = "AWSDirectConnectGatewayAssociation"
    properties: DirectConnectGatewayAssociationNodeProperties = (
        DirectConnectGatewayAssociationNodeProperties()
    )
    sub_resource_relationship: DirectConnectGatewayAssociationToAWSAccountRel = (
        DirectConnectGatewayAssociationToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AssociationToGatewayRel(),
            AssociationToTransitGatewayRel(),
        ],
    )
