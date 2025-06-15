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
class LambdaAliasNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("AliasArn", extra_index=True)
    aliasname: PropertyRef = PropertyRef("Name")
    functionversion: PropertyRef = PropertyRef("FunctionVersion")
    description: PropertyRef = PropertyRef("Description")
    revisionid: PropertyRef = PropertyRef("RevisionId")
    functionarn: PropertyRef = PropertyRef("FunctionArn")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LambdaAliasToFunctionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LambdaAliasToFunctionRel(CartographyRelSchema):
    target_node_label: str = "AWSLambda"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({"id": PropertyRef("FunctionArn")})
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "KNOWN_AS"
    properties: LambdaAliasToFunctionRelProperties = LambdaAliasToFunctionRelProperties()


@dataclass(frozen=True)
class LambdaAliasSchema(CartographyNodeSchema):
    label: str = "AWSLambdaFunctionAlias"
    properties: LambdaAliasNodeProperties = LambdaAliasNodeProperties()
    sub_resource_relationship: LambdaAliasToFunctionRel = LambdaAliasToFunctionRel()
