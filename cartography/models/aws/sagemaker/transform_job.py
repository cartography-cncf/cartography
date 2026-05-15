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
    id: PropertyRef = PropertyRef("TransformJobArn")
    arn: PropertyRef = PropertyRef("TransformJobArn", extra_index=True)
    transform_job_name: PropertyRef = PropertyRef("TransformJobName")
    transform_job_status: PropertyRef = PropertyRef("TransformJobStatus")
    model_name: PropertyRef = PropertyRef("ModelName")
    max_concurrent_transforms: PropertyRef = PropertyRef("MaxConcurrentTransforms")
    max_payload_in_mb: PropertyRef = PropertyRef("MaxPayloadInMB")
    batch_strategy: PropertyRef = PropertyRef("BatchStrategy")
    creation_time: PropertyRef = PropertyRef("CreationTime")
    transform_start_time: PropertyRef = PropertyRef("TransformStartTime")
    transform_end_time: PropertyRef = PropertyRef("TransformEndTime")
    output_data_s3_bucket_id: PropertyRef = PropertyRef("OutputDataS3BucketId")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerTransformJobToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerTransformJobToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "S3Bucket"
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
