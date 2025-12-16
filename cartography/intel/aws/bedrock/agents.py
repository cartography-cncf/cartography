"""
Intel module for AWS Bedrock Agents.
Agents are autonomous AI assistants that can use foundation models, knowledge bases,
and Lambda functions to complete tasks.
"""

import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.aws.bedrock.agent import AWSBedrockAgentSchema
from cartography.models.aws.bedrock.guardrail import GuardrailToCustomModelMatchLink
from cartography.models.aws.bedrock.guardrail import GuardrailToFoundationModelMatchLink
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_agents(
    boto3_session: boto3.session.Session, region: str
) -> List[Dict[str, Any]]:
    """
    Retrieve all agents in AWS Bedrock for a given region.

    This function first lists all agents, then gets detailed information for each agent
    """
    logger.info("Fetching Bedrock agents in region %s", region)
    client = boto3_session.client("bedrock-agent", region_name=region)

    # List all agents (with pagination)
    paginator = client.get_paginator("list_agents")
    agent_summaries = []
    for page in paginator.paginate():
        agent_summaries.extend(page.get("agentSummaries", []))

    logger.info("Found %d agent summaries in region %s", len(agent_summaries), region)

    # Get detailed information for each agent including knowledge bases and action groups
    agents = []
    for summary in agent_summaries:
        agent_id = summary.get("agentId")
        if not agent_id:
            continue

        # Get agent details
        response = client.get_agent(agentId=agent_id)
        agent_details = response.get("agent", {})

        # Get associated knowledge bases
        kb_response = client.list_agent_knowledge_bases(
            agentId=agent_id, agentVersion="DRAFT"
        )
        agent_details["knowledgeBaseSummaries"] = kb_response.get(
            "agentKnowledgeBaseSummaries", []
        )

        # Get action groups and their Lambda function details
        ag_response = client.list_agent_action_groups(
            agentId=agent_id, agentVersion="DRAFT"
        )
        action_group_summaries = ag_response.get("actionGroupSummaries", [])

        # For each action group, get full details to extract Lambda ARN
        action_groups_with_details = []
        for ag_summary in action_group_summaries:
            action_group_id = ag_summary.get("actionGroupId")
            if not action_group_id:
                continue

            ag_details_response = client.get_agent_action_group(
                agentId=agent_id,
                agentVersion="DRAFT",
                actionGroupId=action_group_id,
            )
            action_group_details = ag_details_response.get("agentActionGroup", {})
            action_groups_with_details.append(action_group_details)

        agent_details["actionGroupDetails"] = action_groups_with_details

        agents.append(agent_details)

    logger.info("Retrieved %d agents in region %s", len(agents), region)

    return agents


def transform_agents(
    agents: List[Dict[str, Any]], region: str, account_id: str
) -> List[Dict[str, Any]]:
    """
    Transform agent data for ingestion into the graph.

    Extracts knowledge base ARNs and Lambda function ARNs for relationship creation.
    Also handles guardrail configuration and builds full model ARN.
    """
    for agent in agents:
        agent["Region"] = region

        # Build full model ARN for [:USES_MODEL] relationships
        # The foundationModel field contains just the model ID, we need the full ARN
        model_identifier = agent.get("foundationModel")
        if model_identifier and not model_identifier.startswith("arn:"):
            # It's just a model ID, build the full ARN
            # Check if it's a foundation model (most common) or custom model
            if ":" in model_identifier and not model_identifier.startswith("arn:"):
                # Foundation model format: provider.model-name-version
                agent["foundationModel"] = (
                    f"arn:aws:bedrock:{region}::foundation-model/{model_identifier}"
                )
            # If it's already an ARN or custom model ARN, leave it as is

        # Extract knowledge base ARNs for [:USES_KNOWLEDGE_BASE] relationships
        kb_summaries = agent.get("knowledgeBaseSummaries", [])
        if kb_summaries:
            # Build full ARNs from knowledge base IDs
            kb_arns = []
            for kb in kb_summaries:
                kb_id = kb.get("knowledgeBaseId")
                if kb_id:
                    # Format: arn:aws:bedrock:region:account:knowledge-base/kb-id
                    kb_arn = (
                        f"arn:aws:bedrock:{region}:{account_id}:knowledge-base/{kb_id}"
                    )
                    kb_arns.append(kb_arn)
            agent["knowledge_base_arns"] = kb_arns

        # Extract Lambda function ARNs from action group details for [:INVOKES] relationships
        ag_details = agent.get("actionGroupDetails", [])
        if ag_details:
            lambda_arns = []
            for ag in ag_details:
                # Action group executor can contain a Lambda ARN
                executor = ag.get("actionGroupExecutor", {})
                lambda_arn = executor.get("lambda")
                if lambda_arn:
                    lambda_arns.append(lambda_arn)
            if lambda_arns:
                agent["lambda_function_arns"] = lambda_arns

        # Handle guardrail configuration if present
        guardrail_config = agent.get("guardrailConfiguration", {})
        if guardrail_config:
            guardrail_id = guardrail_config.get("guardrailIdentifier")
            if guardrail_id:
                # Build full ARN from guardrail ID
                # Format: arn:aws:bedrock:region:account:guardrail/guardrail-id
                agent["guardrail_arn"] = (
                    f"arn:aws:bedrock:{region}:{account_id}:guardrail/{guardrail_id}"
                )

    return agents


@timeit
def load_agents(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load agents into the graph database.
    """
    logger.info("Loading %d Bedrock agents for region %s", len(data), region)

    load(
        neo4j_session,
        AWSBedrockAgentSchema(),
        data,
        Region=region,
        AWS_ID=aws_account_id,
        lastupdated=update_tag,
    )


def extract_guardrail_model_links(
    agents: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Extract guardrail-to-model mappings from agent data for creating match links.

    For agents that have both a guardrail and a model configured, we create
    guardrail→model relationships. We distinguish between foundation models
    and custom models based on the ARN format.
    """
    foundation_model_links = []
    custom_model_links = []

    for agent in agents:
        guardrail_arn = agent.get("guardrail_arn")
        model_identifier = agent.get("foundationModel")  # Can be model ID or full ARN
        region = agent.get("Region")

        # Only create link if agent has both guardrail and model
        if not guardrail_arn or not model_identifier:
            continue

        # Build the full model ARN
        # The foundationModel field can contain either:
        # 1. Just the model ID (e.g., "anthropic.claude-3-5-sonnet-20240620-v1:0")
        # 2. A full ARN (e.g., "arn:aws:bedrock:region::foundation-model/model-id" or "arn:aws:bedrock:region:account:custom-model/model-id")
        if model_identifier.startswith("arn:"):
            # It's already a full ARN
            model_arn = model_identifier
        else:
            # It's just a model ID, build the foundation model ARN
            # Foundation models: arn:aws:bedrock:region::foundation-model/model-id (double colon, no account)
            model_arn = f"arn:aws:bedrock:{region}::foundation-model/{model_identifier}"

        # Distinguish between foundation models and custom models by ARN format
        if "::foundation-model/" in model_arn:
            foundation_model_links.append(
                {
                    "guardrail_arn": guardrail_arn,
                    "foundation_model_arn": model_arn,
                }
            )
        elif ":custom-model/" in model_arn:
            custom_model_links.append(
                {
                    "guardrail_arn": guardrail_arn,
                    "custom_model_arn": model_arn,
                }
            )

    return foundation_model_links, custom_model_links


@timeit
def load_guardrail_model_links(
    neo4j_session: neo4j.Session,
    foundation_model_links: List[Dict[str, Any]],
    custom_model_links: List[Dict[str, Any]],
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load guardrail-to-model relationships using match links.

    These relationships are derived from agent data: if a guardrail protects an agent,
    and that agent uses a model, then the guardrail also applies to that model.
    """
    if foundation_model_links:
        logger.info(
            "Creating %d guardrail→foundation model relationships",
            len(foundation_model_links),
        )
        load_matchlinks(
            neo4j_session,
            GuardrailToFoundationModelMatchLink(),
            foundation_model_links,
            _sub_resource_label="AWSBedrockGuardrail",
            _sub_resource_id=aws_account_id,
            lastupdated=update_tag,
        )

    if custom_model_links:
        logger.info(
            "Creating %d guardrail→custom model relationships", len(custom_model_links)
        )
        load_matchlinks(
            neo4j_session,
            GuardrailToCustomModelMatchLink(),
            custom_model_links,
            _sub_resource_label="AWSBedrockGuardrail",
            _sub_resource_id=aws_account_id,
            lastupdated=update_tag,
        )


@timeit
def cleanup_agents(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove stale agent nodes from the graph.
    """
    logger.info("Cleaning up stale Bedrock agents")

    GraphJob.from_node_schema(
        AWSBedrockAgentSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync AWS Bedrock Agents across all specified regions.
    Also creates guardrail-to-model relationships derived from agent configurations.
    """
    logger.info(
        "Syncing Bedrock agents for account %s across %d regions",
        current_aws_account_id,
        len(regions),
    )

    # Collect all transformed agents across regions for match link creation
    all_transformed_agents = []

    for region in regions:
        # Fetch agents from AWS
        agents = get_agents(boto3_session, region)

        if not agents:
            logger.info("No agents found in region %s", region)
            continue

        # Transform data for ingestion
        transformed_agents = transform_agents(agents, region, current_aws_account_id)

        # Load into Neo4j
        load_agents(
            neo4j_session,
            transformed_agents,
            region,
            current_aws_account_id,
            update_tag,
        )

        # Collect for match link creation
        all_transformed_agents.extend(transformed_agents)

    # Create guardrail-to-model relationships using match links
    # These are derived from agents that have both a guardrail and a model configured
    if all_transformed_agents:
        foundation_model_links, custom_model_links = extract_guardrail_model_links(
            all_transformed_agents
        )
        load_guardrail_model_links(
            neo4j_session,
            foundation_model_links,
            custom_model_links,
            current_aws_account_id,
            update_tag,
        )

    # Clean up stale nodes (once, after all regions)
    cleanup_agents(neo4j_session, common_job_parameters)
