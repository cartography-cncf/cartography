from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AWSBedrockCustomModelNodeProperties(CartographyNodeProperties):
    """
    Properties for AWS Bedrock Custom Model nodes.
    """

    id: PropertyRef = PropertyRef("modelArn", description="The ARN of the custom model")
    arn: PropertyRef = PropertyRef(
        "modelArn", extra_index=True, description="The ARN of the custom model"
    )
    model_name: PropertyRef = PropertyRef(
        "modelName", description="The name of the custom model"
    )
    job_arn: PropertyRef = PropertyRef(
        "jobArn", description="The ARN of the training job"
    )
    job_name: PropertyRef = PropertyRef(
        "jobName", description="The name of the training job that created this model"
    )
    base_model_arn: PropertyRef = PropertyRef(
        "baseModelArn",
        description="The ARN of the foundation model this custom model is based on",
    )
    base_model_name: PropertyRef = PropertyRef(
        "baseModelName",
        description="Name of the foundation model customized to produce this model.",
    )
    customization_type: PropertyRef = PropertyRef(
        "customizationType",
        description='The type of customization (e.g., "FINE_TUNING", "CONTINUED_PRE_TRAINING")',
    )
    status: PropertyRef = PropertyRef(
        "modelStatus",
        description="Current status of this `AWSBedrockCustomModel` node.",
    )
    creation_time: PropertyRef = PropertyRef(
        "creationTime", description="The timestamp when the custom model was created"
    )
    training_data_s3_uri: PropertyRef = PropertyRef(
        "trainingDataConfig.s3Uri", description="The S3 URI of the training data"
    )
    output_data_s3_uri: PropertyRef = PropertyRef(
        "outputDataConfig.s3Uri",
        description="The S3 URI where training output is stored",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the custom model exists",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSBedrockCustomModelToAWSAccountRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockCustomModel and AWSAccount.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockCustomModelToAWSAccountRel(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockCustomModel to AWSAccount.
    """

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSBedrockCustomModelToAWSAccountRelProperties = (
        AWSBedrockCustomModelToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockCustomModelToFoundationModelRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockCustomModel and AWSBedrockFoundationModel.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockCustomModelToFoundationModelRel(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockCustomModel to AWSBedrockFoundationModel.
    """

    target_node_label: str = "AWSBedrockFoundationModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("baseModelArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BASED_ON"
    properties: AWSBedrockCustomModelToFoundationModelRelProperties = (
        AWSBedrockCustomModelToFoundationModelRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockCustomModelToS3BucketRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockCustomModel and AWSS3Bucket.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockCustomModelToS3BucketRel(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockCustomModel to AWSS3Bucket (training data source).
    """

    target_node_label: str = "AWSS3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("training_data_bucket_name")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TRAINED_FROM"
    properties: AWSBedrockCustomModelToS3BucketRelProperties = (
        AWSBedrockCustomModelToS3BucketRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockCustomModelSchema(CartographyNodeSchema):
    """
    Schema for AWS Bedrock Custom Model nodes.
    """

    label: str = "AWSBedrockCustomModel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AIModel"])
    properties: AWSBedrockCustomModelNodeProperties = (
        AWSBedrockCustomModelNodeProperties()
    )
    sub_resource_relationship: AWSBedrockCustomModelToAWSAccountRel = (
        AWSBedrockCustomModelToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSBedrockCustomModelToFoundationModelRel(),
            AWSBedrockCustomModelToS3BucketRel(),
        ],
    )
