import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.apigatewayv2.apigatewayv2 import APIGatewayV2APISchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_apigatewayv2_apis(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    client = boto3_session.client("apigatewayv2", region_name=region)
    paginator = client.get_paginator("get_apis")
    apis: list[dict[str, Any]] = []
    for page in paginator.paginate():
        apis.extend(page.get("Items", []))
    return apis


def transform_apigatewayv2_apis(apis: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for api in apis:
        transformed.append(
            {
                "id": api.get("ApiId"),
                "name": api.get("Name"),
                "protocoltype": api.get("ProtocolType"),
                "routeselectionexpression": api.get("RouteSelectionExpression"),
                "apikeyselectionexpression": api.get("ApiKeySelectionExpression"),
                "apiendpoint": api.get("ApiEndpoint"),
                "version": api.get("Version"),
                "createddate": api.get("CreatedDate"),
                "description": api.get("Description"),
            },
        )
    return transformed


@timeit
def load_apigatewayv2_apis(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        APIGatewayV2APISchema(),
        data,
        lastupdated=update_tag,
        AWS_ID=current_aws_account_id,
        region=region,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(
        APIGatewayV2APISchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_apigatewayv2_apis(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    apis = get_apigatewayv2_apis(boto3_session, region)
    transformed = transform_apigatewayv2_apis(apis)
    load_apigatewayv2_apis(
        neo4j_session,
        transformed,
        region,
        current_aws_account_id,
        aws_update_tag,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            f"Syncing AWS APIGatewayV2 APIs for region '{region}' in account '{current_aws_account_id}'.",
        )
        sync_apigatewayv2_apis(
            neo4j_session,
            boto3_session,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
