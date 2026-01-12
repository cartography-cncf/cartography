from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
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

    id: PropertyRef = PropertyRef("modelArn")
    arn: PropertyRef = PropertyRef("modelArn", extra_index=True)
    model_id: PropertyRef = PropertyRef("modelId", extra_index=True)
    model_name: PropertyRef = PropertyRef("modelName")
    provider_name: PropertyRef = PropertyRef("providerName")
    input_modalities: PropertyRef = PropertyRef("inputModalities")
    output_modalities: PropertyRef = PropertyRef("outputModalities")
    response_streaming_supported: PropertyRef = PropertyRef(
        "responseStreamingSupported"
    )
    customizations_supported: PropertyRef = PropertyRef("customizationsSupported")
    inference_types_supported: PropertyRef = PropertyRef("inferenceTypesSupported")
    model_lifecycle_status: PropertyRef = PropertyRef("modelLifecycle.status")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockFoundationModelToAWSAccountRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockFoundationModel and AWSAccount.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockFoundationModelToAWSAccount(CartographyRelSchema):
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
    properties: AWSBedrockFoundationModelNodeProperties = (
        AWSBedrockFoundationModelNodeProperties()
    )
    sub_resource_relationship: AWSBedrockFoundationModelToAWSAccount = (
        AWSBedrockFoundationModelToAWSAccount()
    )
