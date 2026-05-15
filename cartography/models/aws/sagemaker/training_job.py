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
    id: PropertyRef = PropertyRef("TrainingJobArn")
    arn: PropertyRef = PropertyRef("TrainingJobArn", extra_index=True)
    training_job_name: PropertyRef = PropertyRef("TrainingJobName")
    training_job_status: PropertyRef = PropertyRef("TrainingJobStatus")
    secondary_status: PropertyRef = PropertyRef("SecondaryStatus")
    algorithm_specification_training_image: PropertyRef = PropertyRef(
        "AlgorithmSpecification.TrainingImage"
    )
    algorithm_specification_training_input_mode: PropertyRef = PropertyRef(
        "AlgorithmSpecification.TrainingInputMode"
    )
    role_arn: PropertyRef = PropertyRef("RoleArn")
    creation_time: PropertyRef = PropertyRef("CreationTime")
    training_start_time: PropertyRef = PropertyRef("TrainingStartTime")
    training_end_time: PropertyRef = PropertyRef("TrainingEndTime")
    last_modified_time: PropertyRef = PropertyRef("LastModifiedTime")
    billable_time_in_seconds: PropertyRef = PropertyRef("BillableTimeInSeconds")
    training_time_in_seconds: PropertyRef = PropertyRef("TrainingTimeInSeconds")
    enable_network_isolation: PropertyRef = PropertyRef("EnableNetworkIsolation")
    enable_inter_container_traffic_encryption: PropertyRef = PropertyRef(
        "EnableInterContainerTrafficEncryption"
    )
    enable_managed_spot_training: PropertyRef = PropertyRef("EnableManagedSpotTraining")
    input_data_s3_bucket_id: PropertyRef = PropertyRef("InputDataS3BucketId")
    output_data_s3_bucket_id: PropertyRef = PropertyRef("OutputDataS3BucketId")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerTrainingJobToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerTrainingJobToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "S3Bucket"
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
    target_node_label: str = "S3Bucket"
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
