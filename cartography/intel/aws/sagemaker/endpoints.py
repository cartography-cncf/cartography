import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.sagemaker.endpoint import AWSSageMakerEndpointSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_endpoints(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get all SageMaker Endpoints in the given region.
    """
    client = boto3_session.client("sagemaker", region_name=region)
    paginator = client.get_paginator("list_endpoints")
    endpoints: list[dict[str, Any]] = []

    # Get all endpoint names
    endpoint_names: list[str] = []
    for page in paginator.paginate():
        for endpoint in page.get("Endpoints", []):
            endpoint_names.append(endpoint["EndpointName"])

    # Get detailed information for each endpoint
    for endpoint_name in endpoint_names:
        response = client.describe_endpoint(EndpointName=endpoint_name)
        endpoints.append(response)

    return endpoints


def transform_endpoints(
    endpoints: list[dict[str, Any]],
    region: str,
) -> list[dict[str, Any]]:
    """
    Transform endpoint data for loading into Neo4j.
    """
    transformed_endpoints = []

    for endpoint in endpoints:
        transformed_endpoint = {
            "EndpointArn": endpoint.get("EndpointArn"),
            "EndpointName": endpoint.get("EndpointName"),
            "EndpointConfigName": endpoint.get("EndpointConfigName"),
            "EndpointStatus": endpoint.get("EndpointStatus"),
            "CreationTime": endpoint.get("CreationTime"),
            "LastModifiedTime": endpoint.get("LastModifiedTime"),
            "Region": region,
        }
        transformed_endpoints.append(transformed_endpoint)

    return transformed_endpoints


@timeit
def load_endpoints(
    neo4j_session: neo4j.Session,
    endpoints: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load endpoints into Neo4j.
    """
    load(
        neo4j_session,
        AWSSageMakerEndpointSchema(),
        endpoints,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup_endpoints(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove endpoints that no longer exist in AWS.
    """
    GraphJob.from_node_schema(
        AWSSageMakerEndpointSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_endpoints(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync SageMaker Endpoints for all specified regions.
    """
    for region in regions:
        logger.info(
            "Syncing SageMaker Endpoints for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        # Get endpoints from AWS
        endpoints = get_endpoints(boto3_session, region)

        # Transform the data
        transformed_endpoints = transform_endpoints(endpoints, region)

        # Load into Neo4j
        load_endpoints(
            neo4j_session,
            transformed_endpoints,
            region,
            current_aws_account_id,
            aws_update_tag,
        )

    # Cleanup old endpoints
    cleanup_endpoints(neo4j_session, common_job_parameters)
