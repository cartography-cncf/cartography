from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_COGNITO_USER_POOL
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class CognitoUserPoolNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id", description="The id of Cognito User Pool")
    arn: PropertyRef = PropertyRef(
        "Id",
        extra_index=True,
        description="The id of the Cognito User Pool. ListUserPools returns no ARN, so the id is stored here for query convenience",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the Cognito User Pool"
    )
    name: PropertyRef = PropertyRef("Name", description="Name of Cognito User Pool")
    status: PropertyRef = PropertyRef("Status", description="Status of User Pool")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CognitoUserPoolToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CognitoUserPoolToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CognitoUserPoolToAwsAccountRelProperties = (
        CognitoUserPoolToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class CognitoUserPoolSchema(CartographyNodeSchema):
    """Representation of an AWS [Cognito User Pool](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_ListUserPools.html)"""

    label: str = "AWSCognitoUserPool"
    # DEPRECATED: legacy CognitoUserPool node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LEGACY_COGNITO_USER_POOL])
    properties: CognitoUserPoolNodeProperties = CognitoUserPoolNodeProperties()
    sub_resource_relationship: CognitoUserPoolToAWSAccountRel = (
        CognitoUserPoolToAWSAccountRel()
    )
