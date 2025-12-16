"""
AWS Bedrock intel module.
Ingests AWS Bedrock resources including foundation models, custom models,
agents, knowledge bases, guardrails, and provisioned throughput.
"""

import logging
from typing import Dict

import boto3
import neo4j

from cartography.util import timeit

# Import sync functions from individual modules
from . import agents
from . import custom_models
from . import foundation_models
from . import guardrails
from . import knowledge_bases
from . import provisioned_model_throughput

logger = logging.getLogger(__name__)


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
    Main sync function for AWS Bedrock resources.
    Orchestrates ingestion of all Bedrock resource types.

    :param neo4j_session: Neo4j session for database operations
    :param boto3_session: Boto3 session for AWS API calls
    :param regions: List of AWS regions to sync
    :param current_aws_account_id: The AWS account ID being synced
    :param update_tag: Timestamp tag for tracking data freshness
    :param common_job_parameters: Common parameters for cleanup jobs
    """
    logger.info(
        "Syncing AWS Bedrock resources for account %s across %d regions",
        current_aws_account_id,
        len(regions),
    )

    # Sync foundation models
    foundation_models.sync(
        neo4j_session,
        boto3_session,
        regions,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )

    # Sync custom models
    custom_models.sync(
        neo4j_session,
        boto3_session,
        regions,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )

    # Sync guardrails
    guardrails.sync(
        neo4j_session,
        boto3_session,
        regions,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )

    # Sync knowledge bases (before agents, since agents can reference KBs)
    knowledge_bases.sync(
        neo4j_session,
        boto3_session,
        regions,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )

    # Sync agents (after KBs, foundation models, custom models, and guardrails)
    agents.sync(
        neo4j_session,
        boto3_session,
        regions,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )

    # Sync provisioned model throughput
    provisioned_model_throughput.sync(
        neo4j_session,
        boto3_session,
        regions,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )

    logger.info("Completed AWS Bedrock sync for account %s", current_aws_account_id)
