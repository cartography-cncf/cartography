"""
Intel module for AWS Bedrock Guardrails.
Guardrails provide content filtering and safety controls for foundation models,
custom models, and agents.
"""

import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.bedrock.guardrail import AWSBedrockGuardrailSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_guardrails(
    boto3_session: boto3.session.Session, region: str
) -> List[Dict[str, Any]]:
    """
    Retrieve all guardrails in AWS Bedrock for a given region.
    """
    logger.info("Fetching Bedrock guardrails in region %s", region)
    client = boto3_session.client(
        "bedrock",
        region_name=region,
        config=get_botocore_config(),
    )

    paginator = client.get_paginator("list_guardrails")
    guardrails = []
    for page in paginator.paginate():
        guardrails.extend(page.get("guardrails", []))

    logger.info("Retrieved %d guardrails in region %s", len(guardrails), region)

    return guardrails


def transform_guardrails(
    guardrails: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    """
    Transform guardrail data for ingestion into the graph.
    """
    for guardrail in guardrails:
        guardrail["Region"] = region
        # Convert guardrail ID to ARN format for schema compatibility
        # The API returns 'id' but our schema expects 'guardrailId'
        if "id" in guardrail and "guardrailId" not in guardrail:
            guardrail["guardrailId"] = guardrail["id"]
        # Construct full ARN from the id if not already present
        if "arn" in guardrail and "guardrailArn" not in guardrail:
            guardrail["guardrailArn"] = guardrail["arn"]

    return guardrails


@timeit
def load_guardrails(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load guardrails into the graph database.
    """
    logger.info("Loading %d Bedrock guardrails for region %s", len(data), region)

    load(
        neo4j_session,
        AWSBedrockGuardrailSchema(),
        data,
        Region=region,
        AWS_ID=aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup_guardrails(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove stale guardrail nodes from the graph.
    """
    logger.info("Cleaning up stale Bedrock guardrails")

    GraphJob.from_node_schema(
        AWSBedrockGuardrailSchema(),
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
    Sync AWS Bedrock Guardrails across all specified regions.
    """
    logger.info(
        "Syncing Bedrock guardrails for account %s across %d regions",
        current_aws_account_id,
        len(regions),
    )

    for region in regions:
        # Fetch guardrails from AWS
        guardrails = get_guardrails(boto3_session, region)

        if not guardrails:
            logger.info("No guardrails found in region %s", region)
            continue

        # Transform data for ingestion
        transformed_guardrails = transform_guardrails(guardrails, region)

        # Load into Neo4j
        load_guardrails(
            neo4j_session,
            transformed_guardrails,
            region,
            current_aws_account_id,
            update_tag,
        )

    # Clean up stale nodes (once, after all regions)
    cleanup_guardrails(neo4j_session, common_job_parameters)
