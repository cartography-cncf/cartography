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
    id: PropertyRef = PropertyRef(
        "AliasArn", description="The arn of the lambda function alias"
    )
    arn: PropertyRef = PropertyRef(
        "AliasArn", extra_index=True, description="The arn of the lambda function alias"
    )
    aliasname: PropertyRef = PropertyRef(
        "Name", description="The name of the lambda function alias"
    )
    functionversion: PropertyRef = PropertyRef(
        "FunctionVersion", description="The function version that the alias invokes."
    )
    description: PropertyRef = PropertyRef(
        "Description", description="The description of the alias."
    )
    revisionid: PropertyRef = PropertyRef(
        "RevisionId",
        description="A unique identifier that changes when you update the alias.",
    )
    functionarn: PropertyRef = PropertyRef(
        "FunctionArn", description="The ARN of the Lambda function this alias points to"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSLambdaFunctionAliasToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# Standard relationship: AWSLambda --[:KNOWN_AS]--> AWSLambdaFunctionAlias
@dataclass(frozen=True)
class AWSLambdaToAliasRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToAliasRel(CartographyRelSchema):
    "Represents a `KNOWN_AS` relationship from `AWSLambda` to `AWSLambdaFunctionAlias`."

    target_node_label: str = "AWSLambda"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FunctionArn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "KNOWN_AS"
    properties: AWSLambdaToAliasRelProperties = AWSLambdaToAliasRelProperties()


@dataclass(frozen=True)
class AWSLambdaFunctionAliasToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSLambdaFunctionAlias`."

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
    "Represents an `AWSLambdaFunctionAlias` node in the AWS graph."

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
