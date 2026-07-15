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
class InstanceProfileNodeProperties(CartographyNodeProperties):
    """
    Schema describing a InstanceProfile.
    """

    arn: PropertyRef = PropertyRef("Arn", description="The arn")
    createdate: PropertyRef = PropertyRef(
        "CreateDate",
        description="Timestamp when the IAM instance profile was created.",
    )
    id: PropertyRef = PropertyRef("Arn", description="The arn")
    instance_profile_id: PropertyRef = PropertyRef(
        "InstanceProfileId", description="The instance profile id"
    )
    instance_profile_name: PropertyRef = PropertyRef(
        "InstanceProfileName", description="The instance profile name"
    )
    path: PropertyRef = PropertyRef(
        "Path",
        description="IAM path under which the IAM instance profile is organized.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class InstanceProfileToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InstanceProfileToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSInstanceProfile`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: InstanceProfileToAWSAccountRelRelProperties = (
        InstanceProfileToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class InstanceProfileToAWSRoleRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InstanceProfileToAWSRoleRel(CartographyRelSchema):
    "Represents a `ASSOCIATED_WITH` relationship from `AWSInstanceProfile` to `AWSRole`."

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("Roles", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: InstanceProfileToAWSRoleRelRelProperties = (
        InstanceProfileToAWSRoleRelRelProperties()
    )


@dataclass(frozen=True)
class InstanceProfileSchema(CartographyNodeSchema):
    "Represents an `AWSInstanceProfile` node in the AWS graph."

    label: str = "AWSInstanceProfile"
    properties: InstanceProfileNodeProperties = InstanceProfileNodeProperties()
    sub_resource_relationship: InstanceProfileToAWSAccountRel = (
        InstanceProfileToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            InstanceProfileToAWSRoleRel(),
        ]
    )
