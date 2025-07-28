from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AWSLambdaLayerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Arn")
    arn: PropertyRef = PropertyRef("Arn")
    codesize: PropertyRef = PropertyRef("CodeSize")
    signingprofileversionarn: PropertyRef = PropertyRef("SigningProfileVersionArn")
    signingjobarn: PropertyRef = PropertyRef("SigningJobArn")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# Sub-resource relationship: (:AWSAccount)-[:RESOURCE]->(:AWSLambdaLayer)
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


# Matchlink relationship: (:AWSLambda)-[:HAS]->(:AWSLambdaLayer)
@dataclass(frozen=True)
class AWSLambdaToLayerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToLayerRel(CartographyRelSchema):
    target_node_label: str = "AWSLambdaLayer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("Arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS"
    properties: AWSLambdaToLayerRelProperties = AWSLambdaToLayerRelProperties()
    source_node_label: str = "AWSLambda"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("FunctionArn")},
    )


@dataclass(frozen=True)
class AWSLambdaLayerSchema(CartographyNodeSchema):
    label: str = "AWSLambdaLayer"
    properties: AWSLambdaLayerNodeProperties = AWSLambdaLayerNodeProperties()
    sub_resource_relationship: AWSLambdaLayerToAWSAccountRel = (
        AWSLambdaLayerToAWSAccountRel()
    )
