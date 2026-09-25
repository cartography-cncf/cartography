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
class RAMPrincipalAssociationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Id",
        description="Synthetic ID: the resource share ARN and the principal, joined by a pipe",
    )
    resource_share_arn: PropertyRef = PropertyRef(
        "resourceShareArn", description="The ARN of the resource share"
    )
    principal: PropertyRef = PropertyRef(
        "id",
        description=(
            "The ID of the principal that can access the resources in the resource share. "
            "An AWS account ID, or the ARN of an organization, OU, IAM role or IAM user"
        ),
    )
    principal_account_id: PropertyRef = PropertyRef(
        "PrincipalAccountId",
        description="The principal's AWS account ID, when the principal is a bare account ID",
    )
    external: PropertyRef = PropertyRef(
        "external",
        description=(
            "Indicates whether the principal belongs to the same organization "
            "in AWS Organizations as the AWS account that owns the resource share"
        ),
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
class RAMPrincipalAssociationToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RAMPrincipalAssociationToAWSAccountRel(CartographyRelSchema):
    """The account that owns the resource share this association belongs to."""

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RAMPrincipalAssociationToAWSAccountRelProperties = (
        RAMPrincipalAssociationToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class RAMPrincipalAssociationToResourceShareRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RAMPrincipalAssociationToResourceShareRel(CartographyRelSchema):
    target_node_label: str = "AWSRAMResourceShare"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("resourceShareArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: RAMPrincipalAssociationToResourceShareRelProperties = (
        RAMPrincipalAssociationToResourceShareRelProperties()
    )


@dataclass(frozen=True)
class RAMPrincipalToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RAMPrincipalToAWSAccountRel(CartographyRelSchema):
    """
    The account the resource share is shared WITH. This is the relationship that answers
    "who is allowed to consume this share", including accounts outside the organization.
    """

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PrincipalAccountId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SHARED_WITH"
    properties: RAMPrincipalToAWSAccountRelProperties = (
        RAMPrincipalToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class RAMPrincipalAssociationSchema(CartographyNodeSchema):
    """Representation of an AWS RAM [principal association](https://docs.aws.amazon.com/ram/latest/APIReference/API_ListPrincipals.html): an entity allowed to consume a resource share."""

    label: str = "AWSRAMPrincipalAssociation"
    properties: RAMPrincipalAssociationNodeProperties = (
        RAMPrincipalAssociationNodeProperties()
    )
    sub_resource_relationship: RAMPrincipalAssociationToAWSAccountRel = (
        RAMPrincipalAssociationToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RAMPrincipalAssociationToResourceShareRel(),
            RAMPrincipalToAWSAccountRel(),
        ],
    )


# Composite Node Pattern: AWSAccount as known by RAM principal associations.
# Mirrors AWSAccountVPCPeeringSchema in models/aws/ec2/vpc_peering.py: principals can be
# accounts outside the organization, which are otherwise absent from the graph.
@dataclass(frozen=True)
class AWSAccountRAMPrincipalNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The AWS Account ID number")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSAccountRAMPrincipalSchema(CartographyNodeSchema):
    "Represents an AWS account known only as the principal of a RAM resource share."

    # Implementation note:
    # Composite schema targeting the same 'AWSAccount' label as the primary AWS account
    # schema, allowing MERGE operations to combine properties from both sources.
    label: str = "AWSAccount"
    properties: AWSAccountRAMPrincipalNodeProperties = (
        AWSAccountRAMPrincipalNodeProperties()
    )
    # No sub_resource_relationship - accounts are top-level entities
