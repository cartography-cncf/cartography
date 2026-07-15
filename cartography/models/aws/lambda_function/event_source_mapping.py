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
    id: PropertyRef = PropertyRef(
        "UUID", description="The id of the event source mapping"
    )
    batchsize: PropertyRef = PropertyRef(
        "BatchSize",
        description="The maximum number of items to retrieve in a single batch.",
    )
    startingposition: PropertyRef = PropertyRef(
        "StartingPosition",
        description="The position in a stream from which to start reading.",
    )
    startingpositiontimestamp: PropertyRef = PropertyRef(
        "StartingPositionTimestamp", description="The time from which to start reading."
    )
    parallelizationfactor: PropertyRef = PropertyRef(
        "ParallelizationFactor",
        description="The number of batches to process from each shard concurrently.",
    )
    maximumbatchingwindowinseconds: PropertyRef = PropertyRef(
        "MaximumBatchingWindowInSeconds",
        description="The maximum amount of time to gather records before invoking the function, in seconds.",
    )
    eventsourcearn: PropertyRef = PropertyRef(
        "EventSourceArn",
        description="The Amazon Resource Name (ARN) of the event source.",
    )
    lastmodified: PropertyRef = PropertyRef(
        "LastModified",
        description="The date that the event source mapping was last updated, or its state changed.",
    )
    lastprocessingresult: PropertyRef = PropertyRef(
        "LastProcessingResult",
        description="The result of the last AWS Lambda invocation of your Lambda function.",
    )
    state: PropertyRef = PropertyRef(
        "State", description="The state of the event source mapping."
    )
    maximumrecordage: PropertyRef = PropertyRef(
        "MaximumRecordAgeInSeconds",
        description="Discard records older than the specified age.",
    )
    bisectbatchonfunctionerror: PropertyRef = PropertyRef(
        "BisectBatchOnFunctionError",
        description="If the function returns an error, split the batch in two and retry.",
    )
    maximumretryattempts: PropertyRef = PropertyRef(
        "MaximumRetryAttempts",
        description="Discard records after the specified number of retries.",
    )
    tumblingwindowinseconds: PropertyRef = PropertyRef(
        "TumblingWindowInSeconds",
        description="The duration in seconds of a processing window.",
    )
    functionarn: PropertyRef = PropertyRef(
        "FunctionArn", description="The ARN of the Lambda function"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


# (:AWSLambda)-[:RESOURCE]->(:AWSLambdaEventSourceMapping)
# Note:The RESOURCE rel here is not the same as sub-resource relationship. Should rename eventually
@dataclass(frozen=True)
class AWSLambdaToEventSourceMappingRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSLambdaToEventSourceMappingRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSLambda` to `AWSLambdaEventSourceMapping`."

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
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSLambdaEventSourceMapping`."

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
    "Represents an `AWSLambdaEventSourceMapping` node in the AWS graph."

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
