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
class AWSLambdaFunctionAliasNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("AliasArn")
    arn: PropertyRef = PropertyRef("AliasArn", extra_index=True)
    aliasname: PropertyRef = PropertyRef("Name")
    functionversion: PropertyRef = PropertyRef("FunctionVersion")
    description: PropertyRef = PropertyRef("Description")
    revisionid: PropertyRef = PropertyRef("RevisionId")
    functionarn: PropertyRef = PropertyRef("FunctionArn")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaFunctionAliasToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# Standard relationship: AWSLambda --[:KNOWN_AS]--> AWSLambdaFunctionAlias
@dataclass(frozen=True)
class AWSLambdaToAliasRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToAliasRel(CartographyRelSchema):
    target_node_label: str = "AWSLambda"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FunctionArn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "KNOWN_AS"
    properties: AWSLambdaToAliasRelProperties = AWSLambdaToAliasRelProperties()


@dataclass(frozen=True)
class AWSLambdaFunctionAliasToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSLambdaFunctionAliasToAWSAccountRelProperties = (
        AWSLambdaFunctionAliasToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSLambdaFunctionAliasSchema(CartographyNodeSchema):
    label: str = "AWSLambdaFunctionAlias"
    properties: AWSLambdaFunctionAliasNodeProperties = (
        AWSLambdaFunctionAliasNodeProperties()
    )
    sub_resource_relationship: AWSLambdaFunctionAliasToAWSAccountRel = (
        AWSLambdaFunctionAliasToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSLambdaToAliasRel(),
        ]
    )
