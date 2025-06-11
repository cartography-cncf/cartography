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
class TransitGatewayNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ARN")
    arn: PropertyRef = PropertyRef("ARN", extra_index=True)
    tgw_id: PropertyRef = PropertyRef("TgwId", extra_index=True)
    ownerid: PropertyRef = PropertyRef("OwnerId")
    state: PropertyRef = PropertyRef("State")
    description: PropertyRef = PropertyRef("Description")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    shared_account_id: PropertyRef = PropertyRef("SharedAccountId")


@dataclass(frozen=True)
class TransitGatewayToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TransitGatewayToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TransitGatewayToAWSAccountRelProperties = (
        TransitGatewayToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class TransitGatewaySharedWithAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TransitGatewaySharedWithAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("shared_account_id"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SHARED_WITH"
    properties: TransitGatewaySharedWithAccountRelProperties = (
        TransitGatewaySharedWithAccountRelProperties()
    )


@dataclass(frozen=True)
class TransitGatewaySchema(CartographyNodeSchema):
    label: str = "AWSTransitGateway"
    properties: TransitGatewayNodeProperties = TransitGatewayNodeProperties()
    sub_resource_relationship: TransitGatewayToAWSAccountRel = (
        TransitGatewayToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TransitGatewaySharedWithAccountRel(),
        ]
    )


@dataclass(frozen=True)
class TransitGatewayAttachmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("TransitGatewayAttachmentId")
    transit_gateway_attachment_id: PropertyRef = PropertyRef(
        "TransitGatewayAttachmentId", extra_index=True
    )
    transit_gateway_id: PropertyRef = PropertyRef("TransitGatewayId")
    resource_type: PropertyRef = PropertyRef("ResourceType")
    state: PropertyRef = PropertyRef("State")
    vpc_id: PropertyRef = PropertyRef("VpcId")
    subnet_ids: PropertyRef = PropertyRef("SubnetIds")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TGWAttachmentToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TGWAttachmentToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TGWAttachmentToAWSAccountRelProperties = (
        TGWAttachmentToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class TGWAttachmentToTransitGatewayRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TGWAttachmentToTransitGatewayRel(CartographyRelSchema):
    target_node_label: str = "AWSTransitGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "tgw_id": PropertyRef("TransitGatewayId"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: TGWAttachmentToTransitGatewayRelProperties = (
        TGWAttachmentToTransitGatewayRelProperties()
    )


@dataclass(frozen=True)
class TGWAttachmentToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TGWAttachmentToVpcRel(CartographyRelSchema):
    target_node_label: str = "AWSVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("VpcId"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TGWAttachmentToVpcRelProperties = TGWAttachmentToVpcRelProperties()


@dataclass(frozen=True)
class TGWAttachmentToSubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TGWAttachmentToSubnetRel(CartographyRelSchema):
    target_node_label: str = "EC2Subnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "subnetid": PropertyRef("SubnetIds", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_SUBNET"
    properties: TGWAttachmentToSubnetRelProperties = (
        TGWAttachmentToSubnetRelProperties()
    )


@dataclass(frozen=True)
class TransitGatewayAttachmentSchema(CartographyNodeSchema):
    label: str = "AWSTransitGatewayAttachment"
    properties: TransitGatewayAttachmentNodeProperties = (
        TransitGatewayAttachmentNodeProperties()
    )
    sub_resource_relationship: TGWAttachmentToAWSAccountRel = (
        TGWAttachmentToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TGWAttachmentToTransitGatewayRel(),
            TGWAttachmentToVpcRel(),
            TGWAttachmentToSubnetRel(),
        ]
    )
