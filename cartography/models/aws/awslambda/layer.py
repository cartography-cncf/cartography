from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import (
    CartographyRelProperties,
    CartographyRelSchema,
    LinkDirection,
    make_target_node_matcher,
    TargetNodeMatcher,
)


@dataclass(frozen=True)
class LambdaLayerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Arn", extra_index=True)
    arn: PropertyRef = PropertyRef("Arn")
    codesize: PropertyRef = PropertyRef("CodeSize")
    signingprofileversionarn: PropertyRef = PropertyRef("SigningProfileVersionArn")
    signingjobarn: PropertyRef = PropertyRef("SigningJobArn")
    functionarn: PropertyRef = PropertyRef("FunctionArn")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LambdaLayerToFunctionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LambdaLayerToFunctionRel(CartographyRelSchema):
    target_node_label: str = "AWSLambda"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({"id": PropertyRef("FunctionArn")})
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: LambdaLayerToFunctionRelProperties = LambdaLayerToFunctionRelProperties()


@dataclass(frozen=True)
class LambdaLayerSchema(CartographyNodeSchema):
    label: str = "AWSLambdaLayer"
    properties: LambdaLayerNodeProperties = LambdaLayerNodeProperties()
    sub_resource_relationship: LambdaLayerToFunctionRel = LambdaLayerToFunctionRel()
