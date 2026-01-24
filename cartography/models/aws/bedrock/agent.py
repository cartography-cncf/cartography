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
class AWSBedrockAgentNodeProperties(CartographyNodeProperties):
    """
    Properties for AWS Bedrock Agent nodes.
    Agents are autonomous AI assistants that can break down tasks, use tools,
    and search knowledge bases to accomplish goals.
    Based on AWS Bedrock list_agents and get_agent API responses.
    """

    id: PropertyRef = PropertyRef("agentArn")
    arn: PropertyRef = PropertyRef("agentArn", extra_index=True)
    agent_id: PropertyRef = PropertyRef("agentId", extra_index=True)
    agent_name: PropertyRef = PropertyRef("agentName")
    agent_status: PropertyRef = PropertyRef("agentStatus")
    description: PropertyRef = PropertyRef("description")
    instruction: PropertyRef = PropertyRef("instruction")
    foundation_model: PropertyRef = PropertyRef("foundationModel")
    agent_resource_role_arn: PropertyRef = PropertyRef("agentResourceRoleArn")
    idle_session_ttl_in_seconds: PropertyRef = PropertyRef("idleSessionTTLInSeconds")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")
    prepared_at: PropertyRef = PropertyRef("preparedAt")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockAgentToAWSAccountRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockAgent and AWSAccount.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockAgentToAWSAccount(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockAgent to AWSAccount.)
    """

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSBedrockAgentToAWSAccountRelProperties = (
        AWSBedrockAgentToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockAgentToFoundationModelRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockAgent and AWSBedrockFoundationModel.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockAgentToFoundationModel(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockAgent to AWSBedrockFoundationModel.
    Only created when the agent uses a foundation model directly (not via provisioned throughput).
    """

    target_node_label: str = "AWSBedrockFoundationModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("foundation_model_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_MODEL"
    properties: AWSBedrockAgentToFoundationModelRelProperties = (
        AWSBedrockAgentToFoundationModelRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockAgentToCustomModelRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockAgent and AWSBedrockCustomModel.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockAgentToCustomModel(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockAgent to AWSBedrockCustomModel.
    Only created when the agent uses a custom model directly.
    """

    target_node_label: str = "AWSBedrockCustomModel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("custom_model_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_MODEL"
    properties: AWSBedrockAgentToCustomModelRelProperties = (
        AWSBedrockAgentToCustomModelRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockAgentToProvisionedThroughputRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockAgent and AWSBedrockProvisionedModelThroughput.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockAgentToProvisionedThroughput(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockAgent to AWSBedrockProvisionedModelThroughput.
    Created when the agent uses a provisioned throughput for model inference.
    """

    target_node_label: str = "AWSBedrockProvisionedModelThroughput"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("provisioned_model_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_MODEL"
    properties: AWSBedrockAgentToProvisionedThroughputRelProperties = (
        AWSBedrockAgentToProvisionedThroughputRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockAgentToKnowledgeBaseRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockAgent and AWSBedrockKnowledgeBase.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockAgentToKnowledgeBase(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockAgent to AWSBedrockKnowledgeBase.
    """

    target_node_label: str = "AWSBedrockKnowledgeBase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("knowledge_base_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_KNOWLEDGE_BASE"
    properties: AWSBedrockAgentToKnowledgeBaseRelProperties = (
        AWSBedrockAgentToKnowledgeBaseRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockAgentToLambdaRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockAgent and AWSLambda.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockAgentToLambda(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockAgent to AWSLambda (existing Lambda function nodes).
    """

    target_node_label: str = "AWSLambda"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("lambda_function_arns", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "INVOKES"
    properties: AWSBedrockAgentToLambdaRelProperties = (
        AWSBedrockAgentToLambdaRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockAgentToRoleRelProperties(CartographyRelProperties):
    """
    Properties for the relationship between AWSBedrockAgent and AWSRole.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBedrockAgentToRole(CartographyRelSchema):
    """
    Defines the relationship from AWSBedrockAgent to AWSRole (existing IAM role nodes).
    """

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("agentResourceRoleArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: AWSBedrockAgentToRoleRelProperties = (
        AWSBedrockAgentToRoleRelProperties()
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
    """

    target_node_label: str = "AWSBedrockGuardrail"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("guardrail_arn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "APPLIED_TO"
    properties: AWSBedrockGuardrailToAgentRelProperties = (
        AWSBedrockGuardrailToAgentRelProperties()
    )


@dataclass(frozen=True)
class AWSBedrockAgentSchema(CartographyNodeSchema):
    """
    Schema for AWS Bedrock Agent nodes.
    """

    label: str = "AWSBedrockAgent"
    properties: AWSBedrockAgentNodeProperties = AWSBedrockAgentNodeProperties()
    sub_resource_relationship: AWSBedrockAgentToAWSAccount = (
        AWSBedrockAgentToAWSAccount()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSBedrockAgentToFoundationModel(),
            AWSBedrockAgentToCustomModel(),
            AWSBedrockAgentToProvisionedThroughput(),
            AWSBedrockAgentToKnowledgeBase(),
            AWSBedrockAgentToLambda(),
            AWSBedrockAgentToRole(),
            AWSBedrockGuardrailToAgent(),
        ],
    )
