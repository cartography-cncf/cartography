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
class AWSBedrockProvisionedModelThroughputNodeProperties(CartographyNodeProperties):
    """
    Properties for AWS Bedrock Provisioned Model Throughput nodes.
    Represents reserved compute capacity for Bedrock models.
    """

    id: PropertyRef = PropertyRef("provisionedModelArn")
    arn: PropertyRef = PropertyRef("provisionedModelArn", extra_index=True)
    provisioned_model_name: PropertyRef = PropertyRef("provisionedModelName")
    model_arn: PropertyRef = PropertyRef("modelArn")
    desired_model_arn: PropertyRef = PropertyRef("desiredModelArn")
    foundation_model_arn: PropertyRef = PropertyRef("foundationModelArn")
    model_units: PropertyRef = PropertyRef("modelUnits")
    desired_model_units: PropertyRef = PropertyRef("desiredModelUnits")
    status: PropertyRef = PropertyRef("status")
    commitment_duration: PropertyRef = PropertyRef("commitmentDuration")
    commitment_expiration_time: PropertyRef = PropertyRef("commitmentExpirationTime")
    creation_time: PropertyRef = PropertyRef("creationTime")
    last_modified_time: PropertyRef = PropertyRef("lastModifiedTime")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockProvisionedModelThroughputToAWSAccountRelProperties(
    CartographyRelProperties
):
    """
    Properties for the relationship between AWSBedrockProvisionedModelThroughput and AWSAccount.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockProvisionedModelThroughputToAWSAccount(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockProvisionedModelThroughput to AWSAccount.
    """

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSBedrockProvisionedModelThroughputToAWSAccountRelProperties = (
        AWSBedrockProvisionedModelThroughputToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockProvisionedModelThroughputToFoundationModelRelProperties(
    CartographyRelProperties
):
    """
    Properties for the relationship between AWSBedrockProvisionedModelThroughput and AWSBedrockFoundationModel.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockProvisionedModelThroughputToFoundationModel(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockProvisionedModelThroughput to AWSBedrockFoundationModel.
    This relationship is created when the provisioned throughput is for a foundation model.
    """

    target_node_label: str = "AWSBedrockFoundationModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("modelArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PROVIDES_CAPACITY_FOR"
    properties: AWSBedrockProvisionedModelThroughputToFoundationModelRelProperties = (
        AWSBedrockProvisionedModelThroughputToFoundationModelRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockProvisionedModelThroughputToCustomModelRelProperties(
    CartographyRelProperties
):
    """
    Properties for the relationship between AWSBedrockProvisionedModelThroughput and AWSBedrockCustomModel.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockProvisionedModelThroughputToCustomModel(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockProvisionedModelThroughput to AWSBedrockCustomModel.
    This relationship is created when the provisioned throughput is for a custom model.
    """

    target_node_label: str = "AWSBedrockCustomModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("modelArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PROVIDES_CAPACITY_FOR"
    properties: AWSBedrockProvisionedModelThroughputToCustomModelRelProperties = (
        AWSBedrockProvisionedModelThroughputToCustomModelRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockProvisionedModelThroughputSchema(CartographyNodeSchema):
    """
    Schema for AWS Bedrock Provisioned Model Throughput nodes.
    """

    label: str = "AWSBedrockProvisionedModelThroughput"
    properties: AWSBedrockProvisionedModelThroughputNodeProperties = (
        AWSBedrockProvisionedModelThroughputNodeProperties()
    )
    sub_resource_relationship: AWSBedrockProvisionedModelThroughputToAWSAccount = (
        AWSBedrockProvisionedModelThroughputToAWSAccount()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSBedrockProvisionedModelThroughputToFoundationModel(),
            AWSBedrockProvisionedModelThroughputToCustomModel(),
        ],
    )
