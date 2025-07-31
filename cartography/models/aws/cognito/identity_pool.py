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
class CognitoIdentityPoolNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("IdentityPoolId")
    arn: PropertyRef = PropertyRef("IdentityPoolId", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    roles: PropertyRef = PropertyRef("Roles")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CognitoIdentityPoolToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CognitoIdentityPoolToAWSAccountRel(CartographyRelSchema):
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
    label: str = "CognitoIdentityPool"
    properties: CognitoIdentityPoolNodeProperties = CognitoIdentityPoolNodeProperties()
    sub_resource_relationship: CognitoIdentityPoolToAWSAccountRel = (
        CognitoIdentityPoolToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CognitoIdentityPoolToAWSRoleRel(),
        ]
    )
