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
    id: PropertyRef = PropertyRef("Arn")
    arn: PropertyRef = PropertyRef("Arn")
    codesize: PropertyRef = PropertyRef("CodeSize")
    signingprofileversionarn: PropertyRef = PropertyRef("SigningProfileVersionArn")
    signingjobarn: PropertyRef = PropertyRef("SigningJobArn")
    functionarn: PropertyRef = PropertyRef("FunctionArn")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:AWSLambda)-[:HAS]->(:AWSLambdaLayer)
@dataclass(frozen=True)
class AWSLambdaToLayerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToLayerRel(CartographyRelSchema):
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
