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
# Shared relationship properties
# =============================================================================


@dataclass(frozen=True)
class TGWRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# =============================================================================
# AWSTransitGateway
# =============================================================================


@dataclass(frozen=True)
class AWSTransitGatewayNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "TransitGatewayArn", description="Unique identifier of the Transit Gateway"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    arn: PropertyRef = PropertyRef(
        "TransitGatewayArn",
        description="AWS-unique identifier for this object (same as `id`)",
    )
    tgw_id: PropertyRef = PropertyRef(
        "TransitGatewayId", description="Unique identifier of the Transit Gateway"
    )
    ownerid: PropertyRef = PropertyRef(
        "OwnerId",
        description="Identifier of the owner linked to this `AWSTransitGateway` node.",
    )
    state: PropertyRef = PropertyRef("State", description="Can be one of ``pending \\")
    description: PropertyRef = PropertyRef(
        "Description", description="Transit Gateway description"
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="AWS Region containing this `AWSTransitGateway` node.",
    )


# (:AWSAccount)-[:RESOURCE]->(:AWSTransitGateway)
# Uses OwnerId from data (not kwargs) so the RESOURCE rel points to the actual owner account,
# preserving correct semantics for shared TGWs. Cleanup is handled with custom queries
# since GraphJob.from_node_schema() requires set_in_kwargs=True on the sub_resource matcher.
@dataclass(frozen=True)
class AWSTransitGatewayToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSTransitGateway`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OwnerId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TGWRelProperties = TGWRelProperties()


# (:AWSTransitGateway)-[:SHARED_WITH]->(:AWSAccount)
# Only created when OwnerId != current_aws_account_id
@dataclass(frozen=True)
class AWSTransitGatewaySharedWithAccountRel(CartographyRelSchema):
    "Represents a `SHARED_WITH` relationship from `AWSTransitGateway` to `AWSAccount`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_shared_with_account_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SHARED_WITH"
    properties: TGWRelProperties = TGWRelProperties()


@dataclass(frozen=True)
class AWSTransitGatewaySchema(CartographyNodeSchema):
    "Represents an `AWSTransitGateway` node in the AWS graph."

    label: str = "AWSTransitGateway"
    properties: AWSTransitGatewayNodeProperties = AWSTransitGatewayNodeProperties()
    sub_resource_relationship: AWSTransitGatewayToAWSAccountRel = (
        AWSTransitGatewayToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSTransitGatewaySharedWithAccountRel(),
        ]
    )


# =============================================================================
# AWSTransitGatewayAttachment
# =============================================================================


@dataclass(frozen=True)
class AWSTransitGatewayAttachmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "TransitGatewayAttachmentId",
        description="Unique identifier of the Transit Gateway Attachment",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    resource_type: PropertyRef = PropertyRef(
        "ResourceType", description="Can be one of ``vpc \\"
    )
    state: PropertyRef = PropertyRef(
        "State", description="Can be one of ``initiating \\"
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="AWS Region containing this `AWSTransitGatewayAttachment` node.",
    )


# (:AWSAccount)-[:RESOURCE]->(:AWSTransitGatewayAttachment)
@dataclass(frozen=True)
class AWSTransitGatewayAttachmentToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSTransitGatewayAttachment`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TGWRelProperties = TGWRelProperties()


# (:AWSTransitGatewayAttachment)-[:ATTACHED_TO]->(:AWSTransitGateway)
@dataclass(frozen=True)
class AWSTransitGatewayAttachmentToTGWRel(CartographyRelSchema):
    "Represents a `ATTACHED_TO` relationship from `AWSTransitGatewayAttachment` to `AWSTransitGateway`."

    target_node_label: str = "AWSTransitGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"tgw_id": PropertyRef("TransitGatewayId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: TGWRelProperties = TGWRelProperties()


# (:AWSVpc)-[:RESOURCE]->(:AWSTransitGatewayAttachment)
@dataclass(frozen=True)
class AWSTransitGatewayAttachmentToVpcRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSVpc` to `AWSTransitGatewayAttachment`."

    target_node_label: str = "AWSVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VpcId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TGWRelProperties = TGWRelProperties()


# (:AWSTransitGatewayAttachment)-[:PART_OF_SUBNET]->(:AWSEC2Subnet)
@dataclass(frozen=True)
class AWSTransitGatewayAttachmentToSubnetRel(CartographyRelSchema):
    "Represents a `PART_OF_SUBNET` relationship from `AWSTransitGatewayAttachment` to `AWSEC2Subnet`."

    target_node_label: str = "AWSEC2Subnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"subnetid": PropertyRef("SubnetIds", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_SUBNET"
    properties: TGWRelProperties = TGWRelProperties()


@dataclass(frozen=True)
class AWSTransitGatewayAttachmentSchema(CartographyNodeSchema):
    "Represents an `AWSTransitGatewayAttachment` node in the AWS graph."

    label: str = "AWSTransitGatewayAttachment"
    properties: AWSTransitGatewayAttachmentNodeProperties = (
        AWSTransitGatewayAttachmentNodeProperties()
    )
    sub_resource_relationship: AWSTransitGatewayAttachmentToAWSAccountRel = (
        AWSTransitGatewayAttachmentToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSTransitGatewayAttachmentToTGWRel(),
            AWSTransitGatewayAttachmentToVpcRel(),
            AWSTransitGatewayAttachmentToSubnetRel(),
        ]
    )
