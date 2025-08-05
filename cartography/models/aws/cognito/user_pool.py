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
class CognitoUserPoolNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    arn: PropertyRef = PropertyRef("Id", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("Name")
    status: PropertyRef = PropertyRef("Status")
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
    label: str = "CognitoUserPool"
    properties: CognitoUserPoolNodeProperties = CognitoUserPoolNodeProperties()
    sub_resource_relationship: CognitoUserPoolToAWSAccountRel = (
        CognitoUserPoolToAWSAccountRel()
    )
