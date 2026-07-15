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
class AWSLambdaLayerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Arn", description="The arn of the lambda function layer"
    )
    arn: PropertyRef = PropertyRef(
        "Arn", description="The arn of the lambda function layer"
    )
    codesize: PropertyRef = PropertyRef(
        "CodeSize", description="The size of the layer archive in bytes."
    )
    signingprofileversionarn: PropertyRef = PropertyRef(
        "SigningProfileVersionArn",
        description="The Amazon Resource Name (ARN) for a signing profile version.",
    )
    signingjobarn: PropertyRef = PropertyRef(
        "SigningJobArn", description="The Amazon Resource Name (ARN) of a signing job."
    )
    functionarn: PropertyRef = PropertyRef(
        "FunctionArn",
        description="The ARN of the Lambda function this layer belongs to",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


# (:AWSLambda)-[:HAS]->(:AWSLambdaLayer)
@dataclass(frozen=True)
class AWSLambdaToLayerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToLayerRel(CartographyRelSchema):
    "Represents a `HAS` relationship from `AWSLambda` to `AWSLambdaLayer`."

    target_node_label: str = "AWSLambda"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FunctionArn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: AWSLambdaToLayerRelProperties = AWSLambdaToLayerRelProperties()


# (:AWSAccount)-[:RESOURCE]->(:AWSLambdaLayer)
@dataclass(frozen=True)
class AWSLambdaLayerToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaLayerToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSLambdaLayer`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSLambdaLayerToAWSAccountRelProperties = (
        AWSLambdaLayerToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSLambdaLayerSchema(CartographyNodeSchema):
    "Represents an `AWSLambdaLayer` node in the AWS graph."

    label: str = "AWSLambdaLayer"
    properties: AWSLambdaLayerNodeProperties = AWSLambdaLayerNodeProperties()
    sub_resource_relationship: AWSLambdaLayerToAWSAccountRel = (
        AWSLambdaLayerToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSLambdaToLayerRel(),
        ]
    )
