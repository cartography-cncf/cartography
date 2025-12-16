from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
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
class AWSBedrockGuardrailToFoundationModelRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockGuardrail and AWSBedrockFoundationModel.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockGuardrailToFoundationModel(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockGuardrail to AWSBedrockFoundationModel.
    Direction is OUTWARD: (:AWSBedrockGuardrail)-[:APPLIED_TO]->(:AWSBedrockFoundationModel)
    This relationship is created when a guardrail is configured to protect a foundation model.
    """

    target_node_label: str = "AWSBedrockFoundationModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("protected_model_arn", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIED_TO"
    properties: AWSBedrockGuardrailToFoundationModelRelProperties = (
        AWSBedrockGuardrailToFoundationModelRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockGuardrailToCustomModelRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockGuardrail and AWSBedrockCustomModel.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockGuardrailToCustomModel(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockGuardrail to AWSBedrockCustomModel.
    Direction is OUTWARD: (:AWSBedrockGuardrail)-[:APPLIED_TO]->(:AWSBedrockCustomModel)
    This relationship is created when a guardrail is configured to protect a custom model.
    """

    target_node_label: str = "AWSBedrockCustomModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("protected_model_arn", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIED_TO"
    properties: AWSBedrockGuardrailToCustomModelRelProperties = (
        AWSBedrockGuardrailToCustomModelRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockGuardrailToAgentRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockGuardrail and AWSBedrockAgent.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockGuardrailToAgent(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockGuardrail to AWSBedrockAgent.
    Direction is OUTWARD: (:AWSBedrockGuardrail)-[:APPLIED_TO]->(:AWSBedrockAgent)
    This relationship is created when a guardrail is configured to protect an agent.
    """

    target_node_label: str = "AWSBedrockAgent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("protected_agent_arn", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIED_TO"
    properties: AWSBedrockGuardrailToAgentRelProperties = (
        AWSBedrockGuardrailToAgentRelProperties()
    )


# Match link schemas for creating Guardrail→Model relationships
# These are used with load_matchlinks() and derive relationships from agent data


@dataclass(frozen=True)
class GuardrailToFoundationModelMatchLinkRelProperties(CartographyRelProperties):
    """
    Properties for the match link relationship between AWSBedrockGuardrail and AWSBedrockFoundationModel.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardrailToFoundationModelMatchLink(CartographyRelSchema):
    """
    Match link schema for creating (:AWSBedrockGuardrail)-[:APPLIED_TO]->(:AWSBedrockFoundationModel).

    This relationship is created using load_matchlinks(), derived from agents that have
    both a guardrail and a foundation model configured. If a guardrail protects an agent,
    and that agent uses a model, then the guardrail also applies to that model.
    """

    @property
    def source_node_label(self) -> str:
        return "AWSBedrockGuardrail"

    @property
    def source_node_matcher(self) -> SourceNodeMatcher:
        return make_source_node_matcher(
            {"arn": PropertyRef("guardrail_arn")},
        )

    target_node_label: str = "AWSBedrockFoundationModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("foundation_model_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIED_TO"
    properties: GuardrailToFoundationModelMatchLinkRelProperties = (
        GuardrailToFoundationModelMatchLinkRelProperties()
    )


@dataclass(frozen=True)
class GuardrailToCustomModelMatchLinkRelProperties(CartographyRelProperties):
    """
    Properties for the match link relationship between AWSBedrockGuardrail and AWSBedrockCustomModel.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class GuardrailToCustomModelMatchLink(CartographyRelSchema):
    """
    Match link schema for creating (:AWSBedrockGuardrail)-[:APPLIED_TO]->(:AWSBedrockCustomModel).

    This relationship is created using load_matchlinks(), derived from agents that have
    both a guardrail and a custom model configured. If a guardrail protects an agent,
    and that agent uses a model, then the guardrail also applies to that model.
    """

    @property
    def source_node_label(self) -> str:
        return "AWSBedrockGuardrail"

    @property
    def source_node_matcher(self) -> SourceNodeMatcher:
        return make_source_node_matcher(
            {"arn": PropertyRef("guardrail_arn")},
        )

    target_node_label: str = "AWSBedrockCustomModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("custom_model_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIED_TO"
    properties: GuardrailToCustomModelMatchLinkRelProperties = (
        GuardrailToCustomModelMatchLinkRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockGuardrailSchema(CartographyNodeSchema):
    """
    Schema for AWS Bedrock Guardrail nodes.
    Guardrails provide content filtering, safety controls, and policy enforcement
    for foundation models, custom models, and agents.

    The [:APPLIED_TO] relationships are created via:
    - Guardrail→Agent: From agent side using AWSBedrockGuardrailToAgent (in agent.py)
    - Guardrail→Models: Via match links using GuardrailToFoundationModelMatchLink and
      GuardrailToCustomModelMatchLink, derived from agent data
    """

    label: str = "AWSBedrockGuardrail"
    properties: AWSBedrockGuardrailNodeProperties = AWSBedrockGuardrailNodeProperties()
    sub_resource_relationship: AWSBedrockGuardrailToAWSAccount = (
        AWSBedrockGuardrailToAWSAccount()
    )
