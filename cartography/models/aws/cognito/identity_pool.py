from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class CognitoIdentityPoolNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "IdentityPoolId", description="The id of Cognito Identity Pool"
    )
    arn: PropertyRef = PropertyRef(
        "IdentityPoolId",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the Cognito Identity Pool",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The region of the Cognito Identity Pool",
    )
    roles: PropertyRef = PropertyRef(
        "Roles", description="list of aws roles associated with Cognito Identity Pool"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class CognitoIdentityPoolToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CognitoIdentityPoolToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSCognitoIdentityPool`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CognitoIdentityPoolToAwsAccountRelProperties = (
        CognitoIdentityPoolToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class CognitoIdentityPoolToAWSRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CognitoIdentityPoolToAWSRoleRel(CartographyRelSchema):
    "Represents a `ASSOCIATED_WITH` relationship from `AWSCognitoIdentityPool` to `AWSRole`."

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("Roles", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: CognitoIdentityPoolToAWSRoleRelProperties = (
        CognitoIdentityPoolToAWSRoleRelProperties()
    )


@dataclass(frozen=True)
class CognitoIdentityPoolSchema(CartographyNodeSchema):
    "Represents an `AWSCognitoIdentityPool` node in the AWS graph."

    label: str = "AWSCognitoIdentityPool"
    # DEPRECATED: legacy CognitoIdentityPool node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["CognitoIdentityPool"])
    properties: CognitoIdentityPoolNodeProperties = CognitoIdentityPoolNodeProperties()
    sub_resource_relationship: CognitoIdentityPoolToAWSAccountRel = (
        CognitoIdentityPoolToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CognitoIdentityPoolToAWSRoleRel(),
        ]
    )
