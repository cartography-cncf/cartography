import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.sagemaker.endpoint_config import (
    AWSSageMakerEndpointConfigSchema,
)
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_endpoint_configs(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get all SageMaker Endpoint Configs in the given region.
    """
    client = boto3_session.client("sagemaker", region_name=region)
    paginator = client.get_paginator("list_endpoint_configs")
    endpoint_configs: list[dict[str, Any]] = []

    # Get all endpoint config names
    endpoint_config_names: list[str] = []
    for page in paginator.paginate():
        for config in page.get("EndpointConfigs", []):
            endpoint_config_names.append(config["EndpointConfigName"])

    # Get detailed information for each endpoint config
    for config_name in endpoint_config_names:
        response = client.describe_endpoint_config(EndpointConfigName=config_name)
        endpoint_configs.append(response)

    return endpoint_configs


def transform_endpoint_configs(
    endpoint_configs: list[dict[str, Any]],
    region: str,
) -> list[dict[str, Any]]:
    """
    Transform endpoint config data for loading into Neo4j.
    """
    transformed_configs = []

    for config in endpoint_configs:
        # Extract model name from first production variant
        model_name = None
        production_variants = config.get("ProductionVariants", [])
        if production_variants and len(production_variants) > 0:
            model_name = production_variants[0].get("ModelName")

        transformed_config = {
            "EndpointConfigArn": config.get("EndpointConfigArn"),
            "EndpointConfigName": config.get("EndpointConfigName"),
            "CreationTime": config.get("CreationTime"),
            "ModelName": model_name,
            "Region": region,
        }
        transformed_configs.append(transformed_config)

    return transformed_configs


@timeit
def load_endpoint_configs(
    neo4j_session: neo4j.Session,
    endpoint_configs: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load endpoint configs into Neo4j.
    """
    load(
        neo4j_session,
        AWSSageMakerEndpointConfigSchema(),
        endpoint_configs,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup_endpoint_configs(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove endpoint configs that no longer exist in AWS.
    """
    GraphJob.from_node_schema(
        AWSSageMakerEndpointConfigSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_endpoint_configs(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync SageMaker Endpoint Configs for all specified regions.
    """
    for region in regions:
        logger.info(
            "Syncing SageMaker Endpoint Configs for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        # Get endpoint configs from AWS
        endpoint_configs = get_endpoint_configs(boto3_session, region)

        # Transform the data
        transformed_configs = transform_endpoint_configs(endpoint_configs, region)

        # Load into Neo4j
        load_endpoint_configs(
            neo4j_session,
            transformed_configs,
            region,
            current_aws_account_id,
            aws_update_tag,
        )

    # Cleanup old endpoint configs
    cleanup_endpoint_configs(neo4j_session, common_job_parameters)
