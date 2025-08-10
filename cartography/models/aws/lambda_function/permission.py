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
class AWSLambdaPermissionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("FunctionArn")
    function_arn: PropertyRef = PropertyRef("FunctionArn")
    anonymous_access: PropertyRef = PropertyRef("AnonymousAccess")
    anonymous_actions: PropertyRef = PropertyRef("AnonymousActions")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaPermissionToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaPermissionToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSLambdaPermissionToAWSAccountRelProperties = (
        AWSLambdaPermissionToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSLambdaPermissionToAWSLambdaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaPermissionToAWSLambdaRel(CartographyRelSchema):
    target_node_label: str = "AWSLambda"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("FunctionArn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_PERMISSION_POLICY"
    properties: AWSLambdaPermissionToAWSLambdaRelProperties = AWSLambdaPermissionToAWSLambdaRelProperties()


@dataclass(frozen=True)
class AWSLambdaPermissionSchema(CartographyNodeSchema):
    label: str = "AWSLambdaPermission"
    properties: AWSLambdaPermissionNodeProperties = AWSLambdaPermissionNodeProperties()
    sub_resource_relationship: AWSLambdaPermissionToAWSAccountRel = AWSLambdaPermissionToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSLambdaPermissionToAWSLambdaRel(),
        ],
    )
