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
class AWSSageMakerTrainingJobNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "TrainingJobArn", description="The ARN of the Training Job"
    )
    arn: PropertyRef = PropertyRef(
        "TrainingJobArn", extra_index=True, description="The ARN of the Training Job"
    )
    training_job_name: PropertyRef = PropertyRef(
        "TrainingJobName", description="The name of the Training Job"
    )
    training_job_status: PropertyRef = PropertyRef(
        "TrainingJobStatus", description="The status of the Training Job"
    )
    secondary_status: PropertyRef = PropertyRef(
        "SecondaryStatus",
        description="Detailed progress status of the training job.",
    )
    algorithm_specification_training_image: PropertyRef = PropertyRef(
        "AlgorithmSpecification.TrainingImage",
        description="The Docker image for the training algorithm",
    )
    algorithm_specification_training_input_mode: PropertyRef = PropertyRef(
        "AlgorithmSpecification.TrainingInputMode",
        description="How the training algorithm consumes input data.",
    )
    role_arn: PropertyRef = PropertyRef(
        "RoleArn", description="The IAM role ARN used by the training job"
    )
    creation_time: PropertyRef = PropertyRef(
        "CreationTime", description="When the Training Job was created"
    )
    training_start_time: PropertyRef = PropertyRef(
        "TrainingStartTime", description="When training started"
    )
    training_end_time: PropertyRef = PropertyRef(
        "TrainingEndTime", description="When training ended"
    )
    last_modified_time: PropertyRef = PropertyRef(
        "LastModifiedTime",
        description="Timestamp when the training job was last modified.",
    )
    billable_time_in_seconds: PropertyRef = PropertyRef(
        "BillableTimeInSeconds",
        description="Billable duration of the training job in seconds.",
    )
    training_time_in_seconds: PropertyRef = PropertyRef(
        "TrainingTimeInSeconds",
        description="Total training duration in seconds.",
    )
    enable_network_isolation: PropertyRef = PropertyRef(
        "EnableNetworkIsolation",
        description="Whether network isolation is enabled for training containers.",
    )
    enable_inter_container_traffic_encryption: PropertyRef = PropertyRef(
        "EnableInterContainerTrafficEncryption",
        description="Whether traffic between distributed training containers is encrypted.",
    )
    enable_managed_spot_training: PropertyRef = PropertyRef(
        "EnableManagedSpotTraining",
        description="Whether the job uses SageMaker managed spot training.",
    )
    input_data_s3_bucket_id: PropertyRef = PropertyRef(
        "InputDataS3BucketId", description="The S3 bucket ID where input data is stored"
    )
    output_data_s3_bucket_id: PropertyRef = PropertyRef(
        "OutputDataS3BucketId",
        description="The S3 bucket ID where output artifacts are stored",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the Training Job runs",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSSageMakerTrainingJobToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerTrainingJobToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSageMakerTrainingJob`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSageMakerTrainingJobToAWSAccountRelProperties = (
        AWSSageMakerTrainingJobToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerTrainingJobToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerTrainingJobToRoleRel(CartographyRelSchema):
    "Represents a `HAS_EXECUTION_ROLE` relationship from `AWSSageMakerTrainingJob` to `AWSRole`."

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("RoleArn")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_EXECUTION_ROLE"
    properties: AWSSageMakerTrainingJobToRoleRelProperties = (
        AWSSageMakerTrainingJobToRoleRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerTrainingJobToS3BucketReadFromRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerTrainingJobToS3BucketReadFromRel(CartographyRelSchema):
    "Represents a `READS_FROM` relationship from `AWSSageMakerTrainingJob` to `AWSS3Bucket`."

    target_node_label: str = "AWSS3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("InputDataS3BucketId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "READS_FROM"
    properties: AWSSageMakerTrainingJobToS3BucketReadFromRelProperties = (
        AWSSageMakerTrainingJobToS3BucketReadFromRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerTrainingJobToS3BucketProducedModelRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerTrainingJobToS3BucketProducedModelRel(CartographyRelSchema):
    "Represents a `PRODUCES_MODEL_ARTIFACT` relationship from `AWSSageMakerTrainingJob` to `AWSS3Bucket`."

    target_node_label: str = "AWSS3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OutputDataS3BucketId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PRODUCES_MODEL_ARTIFACT"
    properties: AWSSageMakerTrainingJobToS3BucketProducedModelRelProperties = (
        AWSSageMakerTrainingJobToS3BucketProducedModelRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerTrainingJobSchema(CartographyNodeSchema):
    "Represents an `AWSSageMakerTrainingJob` node in the AWS graph."

    label: str = "AWSSageMakerTrainingJob"
    properties: AWSSageMakerTrainingJobNodeProperties = (
        AWSSageMakerTrainingJobNodeProperties()
    )
    sub_resource_relationship: AWSSageMakerTrainingJobToAWSAccountRel = (
        AWSSageMakerTrainingJobToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSSageMakerTrainingJobToRoleRel(),
            AWSSageMakerTrainingJobToS3BucketReadFromRel(),
            AWSSageMakerTrainingJobToS3BucketProducedModelRel(),
        ]
    )
