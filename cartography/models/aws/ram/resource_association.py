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
class RAMResourceAssociationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Id",
        description="Synthetic ID: the resource share ARN and the resource ARN, joined by a pipe",
    )
    resource_share_arn: PropertyRef = PropertyRef(
        "resourceShareArn", description="The ARN of the resource share"
    )
    resource_arn: PropertyRef = PropertyRef(
        "arn",
        extra_index=True,
        description="The ARN of the resource shared through the resource share",
    )
    resource_type: PropertyRef = PropertyRef(
        "type",
        description="The resource type, e.g. 'ec2:TransitGateway' or 'ec2:Subnet'",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="The current status of the association. Valid values: ASSOCIATING, ASSOCIATED, FAILED, DISASSOCIATING, DISASSOCIATED",
    )
    creation_time: PropertyRef = PropertyRef(
        "creationTime", description="The date and time when the association was created"
    )
    last_updated_time: PropertyRef = PropertyRef(
        "lastUpdatedTime",
        description="The date and time when the association was last updated",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the resource share"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RAMResourceAssociationToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RAMResourceAssociationToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RAMResourceAssociationToAWSAccountRelProperties = (
        RAMResourceAssociationToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class RAMResourceAssociationToResourceShareRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RAMResourceAssociationToResourceShareRel(CartographyRelSchema):
    target_node_label: str = "AWSRAMResourceShare"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("resourceShareArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: RAMResourceAssociationToResourceShareRelProperties = (
        RAMResourceAssociationToResourceShareRelProperties()
    )


@dataclass(frozen=True)
class RAMResourceAssociationToTransitGatewayRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RAMResourceAssociationToTransitGatewayRel(CartographyRelSchema):
    """
    Links the association to the shared Transit Gateway when the shared resource is one.
    Other shareable resource types (subnets, license configurations, Route53 resolver rules,
    ...) are not linked yet; the association node still records their ARN and type.
    """

    target_node_label: str = "AWSTransitGateway"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SHARES"
    properties: RAMResourceAssociationToTransitGatewayRelProperties = (
        RAMResourceAssociationToTransitGatewayRelProperties()
    )


@dataclass(frozen=True)
class RAMResourceAssociationSchema(CartographyNodeSchema):
    """Representation of an AWS RAM [resource association](https://docs.aws.amazon.com/ram/latest/APIReference/API_ListResources.html): a resource made available through a resource share."""

    label: str = "AWSRAMResourceAssociation"
    properties: RAMResourceAssociationNodeProperties = (
        RAMResourceAssociationNodeProperties()
    )
    sub_resource_relationship: RAMResourceAssociationToAWSAccountRel = (
        RAMResourceAssociationToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RAMResourceAssociationToResourceShareRel(),
            RAMResourceAssociationToTransitGatewayRel(),
        ],
    )
