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
class AWSBedrockGuardrailNodeProperties(CartographyNodeProperties):
    """
    Properties for AWS Bedrock Guardrail nodes.
    Guardrails provide content filtering and safety controls for models and agents.
    Based on AWS Bedrock list_guardrails and get_guardrail API responses.
    """

    id: PropertyRef = PropertyRef("guardrailArn")
    arn: PropertyRef = PropertyRef("guardrailArn", extra_index=True)
    guardrail_id: PropertyRef = PropertyRef("guardrailId", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    version: PropertyRef = PropertyRef("version")
    status: PropertyRef = PropertyRef("status")
    blocked_input_messaging: PropertyRef = PropertyRef("blockedInputMessaging")
    blocked_outputs_messaging: PropertyRef = PropertyRef("blockedOutputsMessaging")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockGuardrailToAWSAccountRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockGuardrail and AWSAccount.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockGuardrailToAWSAccount(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockGuardrail to AWSAccount.
    Direction is INWARD: (:AWSBedrockGuardrail)<-[:RESOURCE]-(:AWSAccount)
    """

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSBedrockGuardrailToAWSAccountRelProperties = (
        AWSBedrockGuardrailToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockGuardrailSchema(CartographyNodeSchema):
    """
    Schema for AWS Bedrock Guardrail nodes.
    Guardrails provide content filtering, safety controls, and policy enforcement
    for foundation models, custom models, and agents.

    The [:APPLIED_TO] relationship from Guardrail→Agent is created from the Agent side
    using AWSBedrockGuardrailToAgent (defined in agent.py).
    """

    label: str = "AWSBedrockGuardrail"
    properties: AWSBedrockGuardrailNodeProperties = AWSBedrockGuardrailNodeProperties()
    sub_resource_relationship: AWSBedrockGuardrailToAWSAccount = (
        AWSBedrockGuardrailToAWSAccount()
    )
