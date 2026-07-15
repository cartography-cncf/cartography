from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AWSBedrockFoundationModelNodeProperties(CartographyNodeProperties):
    """
    Properties for AWS Bedrock Foundation Model nodes.
    """

    id: PropertyRef = PropertyRef(
        "modelArn", description="The ARN of the foundation model"
    )
    arn: PropertyRef = PropertyRef(
        "modelArn", extra_index=True, description="The ARN of the foundation model"
    )
    model_id: PropertyRef = PropertyRef(
        "modelId",
        extra_index=True,
        description='The model identifier (e.g., "anthropic.claude-3-5-sonnet-20240620-v1:0")',
    )
    model_name: PropertyRef = PropertyRef(
        "modelName", description="The human-readable name of the model"
    )
    provider_name: PropertyRef = PropertyRef(
        "providerName",
        description='The provider of the model (e.g., "Anthropic", "Amazon", "Meta")',
    )
    input_modalities: PropertyRef = PropertyRef(
        "inputModalities",
        description='List of input modalities the model supports (e.g., ["TEXT", "IMAGE"])',
    )
    output_modalities: PropertyRef = PropertyRef(
        "outputModalities",
        description='List of output modalities the model supports (e.g., ["TEXT"])',
    )
    response_streaming_supported: PropertyRef = PropertyRef(
        "responseStreamingSupported",
        description="Whether the model supports streaming responses",
    )
    customizations_supported: PropertyRef = PropertyRef(
        "customizationsSupported",
        description='List of customization types supported (e.g., ["FINE_TUNING"])',
    )
    inference_types_supported: PropertyRef = PropertyRef(
        "inferenceTypesSupported",
        description='List of inference types supported (e.g., ["ON_DEMAND", "PROVISIONED"])',
    )
    model_lifecycle_status: PropertyRef = PropertyRef(
        "modelLifecycle.status",
        description='The lifecycle status of the model (e.g., "ACTIVE", "LEGACY")',
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the model is available",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSBedrockFoundationModelToAWSAccountRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockFoundationModel and AWSAccount.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockFoundationModelToAWSAccountRel(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockFoundationModel to AWSAccount.
    """

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSBedrockFoundationModelToAWSAccountRelProperties = (
        AWSBedrockFoundationModelToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockFoundationModelSchema(CartographyNodeSchema):
    """
    Schema for AWS Bedrock Foundation Model nodes.
    """

    label: str = "AWSBedrockFoundationModel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AIModel"])
    properties: AWSBedrockFoundationModelNodeProperties = (
        AWSBedrockFoundationModelNodeProperties()
    )
    sub_resource_relationship: AWSBedrockFoundationModelToAWSAccountRel = (
        AWSBedrockFoundationModelToAWSAccountRel()
    )
