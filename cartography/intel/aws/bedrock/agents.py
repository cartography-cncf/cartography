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
from cartography.graph.job import GraphJob
from cartography.models.aws.bedrock.agent import AWSBedrockAgentSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

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
    client = boto3_session.client(
        "bedrock-agent",
        region_name=region,
        config=get_botocore_config(),
    )

    # List all agents (with pagination)
    paginator = client.get_paginator("list_agents")
    agent_summaries = []
    for page in paginator.paginate():
        agent_summaries.extend(page.get("agentSummaries", []))

    logger.info("Found %d agent summaries in region %s", len(agent_summaries), region)

    # Get detailed information for each agent including knowledge bases and action groups
    agents = []
    for summary in agent_summaries:
        agent_id = summary["agentId"]

        # Get agent details
        response = client.get_agent(agentId=agent_id)
        agent_details = response.get("agent", {})

        # Get associated knowledge bases (with pagination)
        kb_paginator = client.get_paginator("list_agent_knowledge_bases")
        kb_summaries = []
        for page in kb_paginator.paginate(agentId=agent_id, agentVersion="DRAFT"):
            kb_summaries.extend(page.get("agentKnowledgeBaseSummaries", []))
        agent_details["knowledgeBaseSummaries"] = kb_summaries

        # Get action groups (with pagination)
        ag_paginator = client.get_paginator("list_agent_action_groups")
        action_group_summaries = []
        for page in ag_paginator.paginate(agentId=agent_id, agentVersion="DRAFT"):
            action_group_summaries.extend(page.get("actionGroupSummaries", []))

        # For each action group, get full details to extract Lambda ARN
        action_groups_with_details = []
        for ag_summary in action_group_summaries:
            action_group_id = ag_summary["actionGroupId"]

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
    Also handles guardrail configuration and model identifier parsing.

    The foundationModel field can contain:
    - Base model ID (e.g., "anthropic.claude-v2")
    - Foundation model ARN (arn:aws:bedrock:region::foundation-model/...)
    - Provisioned throughput ARN (arn:aws:bedrock:region:account:provisioned-model/...)
    - Custom model ARN (arn:aws:bedrock:region:account:custom-model/...)
    - Inference profile ARN (not supported yet)
    - Imported model ARN (not supported yet)
    """
    for agent in agents:
        agent["Region"] = region

        # Parse foundationModel to set appropriate relationship fields
        model_identifier = agent.get("foundationModel")
        if model_identifier:
            if model_identifier.startswith("arn:"):
                # Already an ARN - determine type from ARN format
                if "::foundation-model/" in model_identifier:
                    agent["foundation_model_arn"] = model_identifier
                elif ":custom-model/" in model_identifier:
                    agent["custom_model_arn"] = model_identifier
                elif ":provisioned-model/" in model_identifier:
                    agent["provisioned_model_arn"] = model_identifier
                # Skip inference profiles and imported models (would need new node types)
            else:
                # Bare model ID - assume foundation model
                agent["foundation_model_arn"] = (
                    f"arn:aws:bedrock:{region}::foundation-model/{model_identifier}"
                )

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
                # guardrailIdentifier can be ID or ARN
                if guardrail_id.startswith("arn:"):
                    agent["guardrail_arn"] = guardrail_id
                else:
                    # Build full ARN from guardrail ID
                    # Note: Version is not included in ARN - guardrail nodes use base ARN
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
    """
    logger.info(
        "Syncing Bedrock agents for account %s across %d regions",
        current_aws_account_id,
        len(regions),
    )

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

    # Clean up stale nodes (once, after all regions)
    cleanup_agents(neo4j_session, common_job_parameters)
