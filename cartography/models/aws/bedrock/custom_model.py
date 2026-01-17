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
class AWSBedrockCustomModelNodeProperties(CartographyNodeProperties):
    """
    Properties for AWS Bedrock Custom Model nodes.
    """

    id: PropertyRef = PropertyRef("modelArn")
    arn: PropertyRef = PropertyRef("modelArn", extra_index=True)
    model_name: PropertyRef = PropertyRef("modelName")
    job_arn: PropertyRef = PropertyRef("jobArn")
    job_name: PropertyRef = PropertyRef("jobName")
    base_model_arn: PropertyRef = PropertyRef("baseModelArn")
    base_model_name: PropertyRef = PropertyRef("baseModelName")
    customization_type: PropertyRef = PropertyRef("customizationType")
    status: PropertyRef = PropertyRef("modelStatus")
    creation_time: PropertyRef = PropertyRef("creationTime")
    training_data_s3_uri: PropertyRef = PropertyRef("trainingDataConfig.s3Uri")
    output_data_s3_uri: PropertyRef = PropertyRef("outputDataConfig.s3Uri")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockCustomModelToAWSAccountRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockCustomModel and AWSAccount.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockCustomModelToAWSAccount(CartographyRelSchema):
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
class AWSBedrockCustomModelToFoundationModel(CartographyRelSchema):
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
    Properties for the relationship between AWSBedrockCustomModel and S3Bucket.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockCustomModelToS3Bucket(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockCustomModel to S3Bucket (training data source).
    """

    target_node_label: str = "S3Bucket"
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
    properties: AWSBedrockCustomModelNodeProperties = (
        AWSBedrockCustomModelNodeProperties()
    )
    sub_resource_relationship: AWSBedrockCustomModelToAWSAccount = (
        AWSBedrockCustomModelToAWSAccount()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSBedrockCustomModelToFoundationModel(),
            AWSBedrockCustomModelToS3Bucket(),
        ],
    )
