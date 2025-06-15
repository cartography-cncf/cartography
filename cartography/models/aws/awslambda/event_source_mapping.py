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
class LambdaEventSourceMappingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("UUID", extra_index=True)
    batchsize: PropertyRef = PropertyRef("BatchSize")
    startingposition: PropertyRef = PropertyRef("StartingPosition")
    startingpositiontimestamp: PropertyRef = PropertyRef("StartingPositionTimestamp")
    parallelizationfactor: PropertyRef = PropertyRef("ParallelizationFactor")
    maximumbatchingwindowinseconds: PropertyRef = PropertyRef("MaximumBatchingWindowInSeconds")
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


@dataclass(frozen=True)
class LambdaEventSourceMappingToFunctionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LambdaEventSourceMappingToFunctionRel(CartographyRelSchema):
    target_node_label: str = "AWSLambda"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({"id": PropertyRef("FunctionArn")})
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LambdaEventSourceMappingToFunctionRelProperties = LambdaEventSourceMappingToFunctionRelProperties()


@dataclass(frozen=True)
class LambdaEventSourceMappingSchema(CartographyNodeSchema):
    label: str = "AWSLambdaEventSourceMapping"
    properties: LambdaEventSourceMappingNodeProperties = LambdaEventSourceMappingNodeProperties()
    sub_resource_relationship: LambdaEventSourceMappingToFunctionRel = LambdaEventSourceMappingToFunctionRel()
