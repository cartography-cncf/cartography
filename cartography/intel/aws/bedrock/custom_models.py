"""
Intel module for AWS Bedrock Custom Models.
Custom models are foundation models that have been fine-tuned or continued pre-trained
with customer-specific data.
"""

import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.bedrock.custom_model import AWSBedrockCustomModelSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)

# Custom models are only supported in us-east-1 and us-west-2.
# See https://docs.aws.amazon.com/bedrock/latest/userguide/custom-model-supported.html
CUSTOM_MODELS_SUPPORTED_REGIONS = {"us-east-1", "us-west-2"}


@timeit
@aws_handle_regions
def get_custom_models(
    boto3_session: boto3.session.Session, region: str
) -> List[Dict[str, Any]]:
    """
    Retrieve all custom models in AWS Bedrock for a given region.

    Uses pagination for list_custom_models and calls get_custom_model for each
    to retrieve full details (jobArn, jobName, trainingDataConfig, outputDataConfig).
    """
    if region not in CUSTOM_MODELS_SUPPORTED_REGIONS:
        logger.debug(
            "Bedrock custom models not supported in region %s. Skipping.",
            region,
        )
        return []

    logger.info("Fetching Bedrock custom models in region %s", region)
    client = boto3_session.client(
        "bedrock",
        region_name=region,
        config=get_botocore_config(),
    )

    # Use pagination for list_custom_models
    paginator = client.get_paginator("list_custom_models")
    model_summaries = []
    for page in paginator.paginate():
        model_summaries.extend(page.get("modelSummaries", []))

    # Get full details for each model (includes jobArn, trainingDataConfig, etc.)
    models = []
    for summary in model_summaries:
        model_arn = summary["modelArn"]
        response = client.get_custom_model(modelIdentifier=model_arn)
        models.append(response)

    logger.info("Retrieved %d custom models in region %s", len(models), region)

    return models


def transform_custom_models(
    models: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    """
    Transform custom model data for ingestion into the graph.
    """
    for model in models:
        model["Region"] = region

        # Extract training bucket name from S3 URI for TRAINED_FROM relationship
        training_s3_uri = model.get("trainingDataConfig", {}).get("s3Uri", "")
        if training_s3_uri and training_s3_uri.startswith("s3://"):
            # Parse bucket name from s3://bucket-name/path
            bucket_name = training_s3_uri.split("/")[2]
            model["training_data_bucket_name"] = bucket_name

    return models


@timeit
def load_custom_models(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load custom models into the graph database.
    """
    logger.info("Loading %d Bedrock custom models for region %s", len(data), region)

    load(
        neo4j_session,
        AWSBedrockCustomModelSchema(),
        data,
        Region=region,
        AWS_ID=aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup_custom_models(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove stale custom model nodes from the graph.
    """
    logger.info("Cleaning up stale Bedrock custom models")

    GraphJob.from_node_schema(
        AWSBedrockCustomModelSchema(),
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
    Sync AWS Bedrock Custom Models across all specified regions.
    """
    logger.info(
        "Syncing Bedrock custom models for account %s across %d regions",
        current_aws_account_id,
        len(regions),
    )

    for region in regions:
        # Fetch custom models from AWS
        models = get_custom_models(boto3_session, region)

        if not models:
            logger.info("No custom models found in region %s", region)
            continue

        # Transform data for ingestion
        transformed_models = transform_custom_models(models, region)

        # Load into Neo4j
        load_custom_models(
            neo4j_session,
            transformed_models,
            region,
            current_aws_account_id,
            update_tag,
        )

    # Clean up stale nodes (once, after all regions)
    cleanup_custom_models(neo4j_session, common_job_parameters)
