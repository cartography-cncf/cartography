from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class RAMResourceShareNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "resourceShareArn", description="The ARN of the resource share"
    )
    arn: PropertyRef = PropertyRef(
        "resourceShareArn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the resource share",
    )
    name: PropertyRef = PropertyRef(
        "name", description="The name of the resource share"
    )
    owning_account_id: PropertyRef = PropertyRef(
        "owningAccountId",
        description="The ID of the AWS account that owns the resource share",
    )
    allow_external_principals: PropertyRef = PropertyRef(
        "allowExternalPrincipals",
        description=(
            "Indicates whether principals outside your organization in AWS Organizations "
            "can be associated with a resource share"
        ),
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="The current status of the resource share. Valid values: PENDING, ACTIVE, FAILED, DELETING, DELETED",
    )
    status_message: PropertyRef = PropertyRef(
        "statusMessage", description="A message about the status of the resource share"
    )
    creation_time: PropertyRef = PropertyRef(
        "creationTime",
        description="The date and time when the resource share was created",
    )
    last_updated_time: PropertyRef = PropertyRef(
        "lastUpdatedTime",
        description="The date and time when the resource share was last updated",
    )
    feature_set: PropertyRef = PropertyRef(
        "featureSet",
        description=(
            "Indicates what features are available for this resource share. "
            "Valid values: CREATED_FROM_POLICY, PROMOTING_TO_STANDARD, STANDARD"
        ),
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the resource share"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RAMResourceShareToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RAMResourceShareToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RAMResourceShareToAWSAccountRelProperties = (
        RAMResourceShareToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class RAMResourceShareSchema(CartographyNodeSchema):
    """Representation of an AWS [RAM ResourceShare](https://docs.aws.amazon.com/ram/latest/APIReference/API_ResourceShare.html)"""

    label: str = "AWSRAMResourceShare"
    properties: RAMResourceShareNodeProperties = RAMResourceShareNodeProperties()
    sub_resource_relationship: RAMResourceShareToAWSAccountRel = (
        RAMResourceShareToAWSAccountRel()
    )
