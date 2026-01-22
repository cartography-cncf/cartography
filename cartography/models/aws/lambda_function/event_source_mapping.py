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
class AWSLambdaEventSourceMappingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("UUID")
    batchsize: PropertyRef = PropertyRef("BatchSize")
    startingposition: PropertyRef = PropertyRef("StartingPosition")
    startingpositiontimestamp: PropertyRef = PropertyRef("StartingPositionTimestamp")
    parallelizationfactor: PropertyRef = PropertyRef("ParallelizationFactor")
    maximumbatchingwindowinseconds: PropertyRef = PropertyRef(
        "MaximumBatchingWindowInSeconds"
    )
    eventsourcearn: PropertyRef = PropertyRef("EventSourceArn")
    lastmodified: PropertyRef = PropertyRef("LastModified")
    lastprocessingresult: PropertyRef = PropertyRef("LastProcessingResult")
    state: PropertyRef = PropertyRef("State")
    maximumrecordage: PropertyRef = PropertyRef("MaximumRecordAgeInSeconds")
    bisectbatchonfunctionerror: PropertyRef = PropertyRef("BisectBatchOnFunctionError")
    maximumretryattempts: PropertyRef = PropertyRef("MaximumRetryAttempts")
    tumblingwindowinseconds: PropertyRef = PropertyRef("TumblingWindowInSeconds")
    functionarn: PropertyRef = PropertyRef("FunctionArn")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:AWSLambda)-[:RESOURCE]->(:AWSLambdaEventSourceMapping)
# Note:The RESOURCE rel here is not the same as sub-resource relationship. Should rename eventually
@dataclass(frozen=True)
class AWSLambdaToEventSourceMappingRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToEventSourceMappingRel(CartographyRelSchema):
    target_node_label: str = "AWSLambda"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FunctionArn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSLambdaToEventSourceMappingRelProperties = (
        AWSLambdaToEventSourceMappingRelProperties()
    )


# Sub-resource relationship: (:AWSAccount)-[:RESOURCE]->(:AWSLambdaEventSourceMapping)
@dataclass(frozen=True)
class AWSLambdaEventSourceMappingToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaEventSourceMappingToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSLambdaEventSourceMappingToAWSAccountRelProperties = (
        AWSLambdaEventSourceMappingToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSLambdaEventSourceMappingSchema(CartographyNodeSchema):
    label: str = "AWSLambdaEventSourceMapping"
    properties: AWSLambdaEventSourceMappingNodeProperties = (
        AWSLambdaEventSourceMappingNodeProperties()
    )
    sub_resource_relationship: AWSLambdaEventSourceMappingToAWSAccountRel = (
        AWSLambdaEventSourceMappingToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSLambdaToEventSourceMappingRel(),
        ]
    )
