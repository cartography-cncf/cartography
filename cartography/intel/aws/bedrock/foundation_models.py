"""
Intel module for AWS Bedrock Foundation Models.
Foundation models are base models provided by model providers (Anthropic, Meta, AI21, etc.)
through Amazon Bedrock. These are pre-trained models that can be used directly or
customized through fine-tuning or continued pre-training.
"""

import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.bedrock.foundation_model import (
    AWSBedrockFoundationModelSchema,
)
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_foundation_models(
    boto3_session: boto3.session.Session, region: str
) -> List[Dict[str, Any]]:
    """
    Retrieve all foundation models available in AWS Bedrock for a given region.
    """
    logger.info("Fetching Bedrock foundation models in region %s", region)
    client = boto3_session.client(
        "bedrock",
        region_name=region,
        config=get_botocore_config(),
    )

    # list_foundation_models returns all models in a single response (no pagination)
    response = client.list_foundation_models()
    models = response.get("modelSummaries", [])

    logger.info("Retrieved %d foundation models in region %s", len(models), region)

    return models


def transform_foundation_models(
    models: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    """
    Transform foundation model data for ingestion into the graph.
    """
    for model in models:
        model["Region"] = region

    return models


@timeit
def load_foundation_models(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load foundation models into the graph database.
    """
    logger.info("Loading %d Bedrock foundation models for region %s", len(data), region)

    load(
        neo4j_session,
        AWSBedrockFoundationModelSchema(),
        data,
        Region=region,
        AWS_ID=aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup_foundation_models(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove stale foundation model nodes from the graph.
    """
    logger.info("Cleaning up stale Bedrock foundation models")

    GraphJob.from_node_schema(
        AWSBedrockFoundationModelSchema(),
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
    Sync AWS Bedrock Foundation Models across all specified regions.
    """
    logger.info(
        "Syncing Bedrock foundation models for account %s across %d regions",
        current_aws_account_id,
        len(regions),
    )

    for region in regions:
        # Fetch foundation models from AWS
        models = get_foundation_models(boto3_session, region)

        if not models:
            logger.info("No foundation models found in region %s", region)
            continue

        # Transform data for ingestion
        transformed_models = transform_foundation_models(models, region)

        # Load into Neo4j
        load_foundation_models(
            neo4j_session,
            transformed_models,
            region,
            current_aws_account_id,
            update_tag,
        )

    # Clean up stale nodes (once, after all regions)
    cleanup_foundation_models(neo4j_session, common_job_parameters)
