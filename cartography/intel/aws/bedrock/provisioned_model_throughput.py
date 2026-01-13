"""
Intel module for AWS Bedrock Provisioned Model Throughput.
Provisioned throughput provides reserved capacity for foundation models and custom models,
ensuring consistent performance and availability.
"""

import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.bedrock.provisioned_model_throughput import (
    AWSBedrockProvisionedModelThroughputSchema,
)
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_provisioned_throughputs(
    boto3_session: boto3.session.Session, region: str
) -> List[Dict[str, Any]]:
    """
    Retrieve all provisioned model throughputs in AWS Bedrock for a given region.
    """
    logger.info("Fetching Bedrock provisioned model throughputs in region %s", region)
    client = boto3_session.client(
        "bedrock",
        region_name=region,
        config=get_botocore_config(),
    )

    # List all provisioned throughputs (with pagination)
    paginator = client.get_paginator("list_provisioned_model_throughputs")
    throughput_summaries = []
    for page in paginator.paginate():
        throughput_summaries.extend(page.get("provisionedModelSummaries", []))

    logger.info(
        "Found %d provisioned throughput summaries in region %s",
        len(throughput_summaries),
        region,
    )

    # Get detailed information for each provisioned throughput
    throughputs = []
    for summary in throughput_summaries:
        throughput_arn = summary["provisionedModelArn"]
        response = client.get_provisioned_model_throughput(
            provisionedModelId=throughput_arn
        )
        # The response contains the fields directly (no nested object)
        throughputs.append(response)

    logger.info(
        "Retrieved %d provisioned throughputs in region %s", len(throughputs), region
    )

    return throughputs


def transform_provisioned_throughputs(
    throughputs: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    """
    Transform provisioned throughput data for ingestion into the graph.
    """
    for throughput in throughputs:
        throughput["Region"] = region

    return throughputs


@timeit
def load_provisioned_throughputs(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load provisioned model throughputs into the graph database.
    """
    logger.info(
        "Loading %d Bedrock provisioned throughputs for region %s", len(data), region
    )

    load(
        neo4j_session,
        AWSBedrockProvisionedModelThroughputSchema(),
        data,
        Region=region,
        AWS_ID=aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup_provisioned_throughputs(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove stale provisioned throughput nodes from the graph.
    """
    logger.info("Cleaning up stale Bedrock provisioned throughputs")

    GraphJob.from_node_schema(
        AWSBedrockProvisionedModelThroughputSchema(),
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
    Sync AWS Bedrock Provisioned Model Throughputs across all specified regions.
    """
    logger.info(
        "Syncing Bedrock provisioned throughputs for account %s across %d regions",
        current_aws_account_id,
        len(regions),
    )

    for region in regions:
        # Fetch provisioned throughputs from AWS
        throughputs = get_provisioned_throughputs(boto3_session, region)

        if not throughputs:
            logger.info("No provisioned throughputs found in region %s", region)
            continue

        # Transform data for ingestion
        transformed_throughputs = transform_provisioned_throughputs(throughputs, region)

        # Load into Neo4j
        load_provisioned_throughputs(
            neo4j_session,
            transformed_throughputs,
            region,
            current_aws_account_id,
            update_tag,
        )

    # Clean up stale nodes (once, after all regions)
    cleanup_provisioned_throughputs(neo4j_session, common_job_parameters)
