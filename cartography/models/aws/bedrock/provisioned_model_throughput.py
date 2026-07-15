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

    id: PropertyRef = PropertyRef(
        "provisionedModelArn", description="The ARN of the provisioned throughput"
    )
    arn: PropertyRef = PropertyRef(
        "provisionedModelArn",
        extra_index=True,
        description="The ARN of the provisioned throughput",
    )
    provisioned_model_name: PropertyRef = PropertyRef(
        "provisionedModelName",
        description="The name of the provisioned model throughput",
    )
    model_arn: PropertyRef = PropertyRef(
        "modelArn", description="The ARN of the model (foundation or custom)"
    )
    desired_model_arn: PropertyRef = PropertyRef(
        "desiredModelArn", description="The desired model ARN (used during updates)"
    )
    foundation_model_arn: PropertyRef = PropertyRef(
        "foundationModelArn", description="The ARN of the foundation model"
    )
    model_units: PropertyRef = PropertyRef(
        "modelUnits", description="The number of model units allocated"
    )
    desired_model_units: PropertyRef = PropertyRef(
        "desiredModelUnits",
        description="The desired number of model units (used during updates)",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description='The status of the provisioned throughput (e.g., "Creating", "InService", "Updating")',
    )
    commitment_duration: PropertyRef = PropertyRef(
        "commitmentDuration",
        description='The commitment duration for the purchase (e.g., "OneMonth", "SixMonths")',
    )
    commitment_expiration_time: PropertyRef = PropertyRef(
        "commitmentExpirationTime",
        description="The timestamp when the commitment expires",
    )
    creation_time: PropertyRef = PropertyRef(
        "creationTime",
        description="The timestamp when the provisioned throughput was created",
    )
    last_modified_time: PropertyRef = PropertyRef(
        "lastModifiedTime",
        description="The timestamp when the provisioned throughput was last modified",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the provisioned throughput exists",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSBedrockProvisionedModelThroughputToAWSAccountRelProperties(
    CartographyRelProperties
):
    """
    Properties for the relationship between AWSBedrockProvisionedModelThroughput and AWSAccount.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockProvisionedModelThroughputToAWSAccountRel(CartographyRelSchema):
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
class AWSBedrockProvisionedModelThroughputToFoundationModelRel(CartographyRelSchema):
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
class AWSBedrockProvisionedModelThroughputToCustomModelRel(CartographyRelSchema):
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
    sub_resource_relationship: AWSBedrockProvisionedModelThroughputToAWSAccountRel = (
        AWSBedrockProvisionedModelThroughputToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSBedrockProvisionedModelThroughputToFoundationModelRel(),
            AWSBedrockProvisionedModelThroughputToCustomModelRel(),
        ],
    )
