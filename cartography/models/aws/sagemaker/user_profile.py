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
class AWSSageMakerUserProfileNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "UserProfileArn", description="The ARN of the User Profile"
    )
    arn: PropertyRef = PropertyRef(
        "UserProfileArn", extra_index=True, description="The ARN of the User Profile"
    )
    user_profile_name: PropertyRef = PropertyRef(
        "UserProfileName", description="The name of the User Profile"
    )
    domain_id: PropertyRef = PropertyRef(
        "DomainId", description="The Domain ID that this profile belongs to"
    )
    status: PropertyRef = PropertyRef(
        "Status", description="The status of the User Profile"
    )
    creation_time: PropertyRef = PropertyRef(
        "CreationTime", description="When the User Profile was created"
    )
    last_modified_time: PropertyRef = PropertyRef(
        "LastModifiedTime", description="When the User Profile was last modified"
    )
    execution_role: PropertyRef = PropertyRef(
        "ExecutionRole", description="The IAM execution role ARN for the user"
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the User Profile exists",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSSageMakerUserProfileToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerUserProfileToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSageMakerUserProfile`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSageMakerUserProfileToAWSAccountRelProperties = (
        AWSSageMakerUserProfileToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerUserProfileToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerUserProfileToRoleRel(CartographyRelSchema):
    "Represents a `HAS_EXECUTION_ROLE` relationship from `AWSSageMakerUserProfile` to `AWSRole`."

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("ExecutionRole")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_EXECUTION_ROLE"
    properties: AWSSageMakerUserProfileToRoleRelProperties = (
        AWSSageMakerUserProfileToRoleRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerUserProfileToAWSSageMakerDomainRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerUserProfileToAWSSageMakerDomainRel(CartographyRelSchema):
    "Represents a `CONTAINS` relationship from `AWSSageMakerDomain` to `AWSSageMakerUserProfile`."

    target_node_label: str = "AWSSageMakerDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"domain_id": PropertyRef("DomainId")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AWSSageMakerUserProfileToAWSSageMakerDomainRelProperties = (
        AWSSageMakerUserProfileToAWSSageMakerDomainRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerUserProfileSchema(CartographyNodeSchema):
    "Represents an `AWSSageMakerUserProfile` node in the AWS graph."

    label: str = "AWSSageMakerUserProfile"
    properties: AWSSageMakerUserProfileNodeProperties = (
        AWSSageMakerUserProfileNodeProperties()
    )
    sub_resource_relationship: AWSSageMakerUserProfileToAWSAccountRel = (
        AWSSageMakerUserProfileToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSSageMakerUserProfileToRoleRel(),
            AWSSageMakerUserProfileToAWSSageMakerDomainRel(),
        ]
    )
