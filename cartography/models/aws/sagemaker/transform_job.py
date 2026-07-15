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
class AWSSageMakerTransformJobNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "TransformJobArn", description="The ARN of the Transform Job"
    )
    arn: PropertyRef = PropertyRef(
        "TransformJobArn", extra_index=True, description="The ARN of the Transform Job"
    )
    transform_job_name: PropertyRef = PropertyRef(
        "TransformJobName", description="The name of the Transform Job"
    )
    transform_job_status: PropertyRef = PropertyRef(
        "TransformJobStatus", description="The status of the Transform Job"
    )
    model_name: PropertyRef = PropertyRef(
        "ModelName", description="The name of the model used for the transform"
    )
    max_concurrent_transforms: PropertyRef = PropertyRef(
        "MaxConcurrentTransforms",
        description="Maximum number of concurrent transform requests.",
    )
    max_payload_in_mb: PropertyRef = PropertyRef(
        "MaxPayloadInMB",
        description="Maximum transform request payload size in MiB.",
    )
    batch_strategy: PropertyRef = PropertyRef(
        "BatchStrategy",
        description="Strategy used to split input records into transform batches.",
    )
    creation_time: PropertyRef = PropertyRef(
        "CreationTime", description="When the Transform Job was created"
    )
    transform_start_time: PropertyRef = PropertyRef(
        "TransformStartTime",
        description="Timestamp when the batch transform job started.",
    )
    transform_end_time: PropertyRef = PropertyRef(
        "TransformEndTime",
        description="Timestamp when the batch transform job completed.",
    )
    output_data_s3_bucket_id: PropertyRef = PropertyRef(
        "OutputDataS3BucketId",
        description="The S3 bucket ID where transform output is stored",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the Transform Job runs",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSSageMakerTransformJobToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerTransformJobToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSageMakerTransformJob`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSageMakerTransformJobToAWSAccountRelProperties = (
        AWSSageMakerTransformJobToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerTransformJobToModelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerTransformJobToModelRel(CartographyRelSchema):
    "Represents a `USES` relationship from `AWSSageMakerTransformJob` to `AWSSageMakerModel`."

    target_node_label: str = "AWSSageMakerModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"model_name": PropertyRef("ModelName")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES"
    properties: AWSSageMakerTransformJobToModelRelProperties = (
        AWSSageMakerTransformJobToModelRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerTransformJobToS3BucketRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerTransformJobToS3BucketRel(CartographyRelSchema):
    "Represents a `WRITES_TO` relationship from `AWSSageMakerTransformJob` to `AWSS3Bucket`."

    target_node_label: str = "AWSS3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OutputDataS3BucketId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WRITES_TO"
    properties: AWSSageMakerTransformJobToS3BucketRelProperties = (
        AWSSageMakerTransformJobToS3BucketRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerTransformJobSchema(CartographyNodeSchema):
    "Represents an `AWSSageMakerTransformJob` node in the AWS graph."

    label: str = "AWSSageMakerTransformJob"
    properties: AWSSageMakerTransformJobNodeProperties = (
        AWSSageMakerTransformJobNodeProperties()
    )
    sub_resource_relationship: AWSSageMakerTransformJobToAWSAccountRel = (
        AWSSageMakerTransformJobToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSSageMakerTransformJobToModelRel(),
            AWSSageMakerTransformJobToS3BucketRel(),
        ]
    )
