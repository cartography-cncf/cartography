import logging
from typing import Any

import boto3
import neo4j
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectionClosedError
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import ReadTimeoutError
from botocore.parsers import ResponseParserError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.apigatewayv2.apigatewayv2 import APIGatewayV2APISchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

_RETRYABLE_HTTP_STATUS_CODES = {429, 500, 502, 503, 504}


class APIGatewayV2TransientRegionFailure(Exception):
    pass


def _is_retryable_apigatewayv2_error(error: ClientError) -> bool:
    error_code = error.response.get("Error", {}).get("Code", "")
    error_message = error.response.get("Error", {}).get("Message", "")
    status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    return (
        error_code
        in {
            "InternalFailure",
            "InternalServerException",
            "RequestLimitExceeded",
            "RequestThrottled",
            "RequestTimeout",
            "RequestTimeoutException",
            "ServiceException",
            "ServiceUnavailable",
            "ServiceUnavailableException",
            "Throttling",
            "ThrottlingException",
            "TooManyRequestsException",
        }
        or status_code in _RETRYABLE_HTTP_STATUS_CODES
        or (
            error_code == "AuthorizerConfigurationException"
            and "internal server error" in str(error_message).lower()
        )
    )


@timeit
@aws_handle_regions
def get_apigatewayv2_apis(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    client = create_boto3_client(boto3_session, "apigatewayv2", region_name=region)
    paginator = client.get_paginator("get_apis")
    apis: list[dict[str, Any]] = []
    try:
        for page in paginator.paginate():
            apis.extend(page.get("Items", []))
    except ClientError as error:
        if _is_retryable_apigatewayv2_error(error):
            raise APIGatewayV2TransientRegionFailure(
                "AWS SDK retries were exhausted for transient GetApis failure"
            ) from error
        raise
    except (
        ConnectionClosedError,
        ConnectTimeoutError,
        ReadTimeoutError,
        ResponseParserError,
    ) as error:
        raise APIGatewayV2TransientRegionFailure(
            "Encountered a transient regional API Gateway v2 endpoint failure while calling GetApis"
        ) from error
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
    cleanup_safe = True
    for region in regions:
        logger.info(
            f"Syncing AWS APIGatewayV2 APIs for region '{region}' in account '{current_aws_account_id}'.",
        )
        try:
            sync_apigatewayv2_apis(
                neo4j_session,
                boto3_session,
                region,
                current_aws_account_id,
                update_tag,
            )
        except APIGatewayV2TransientRegionFailure as error:
            cleanup_safe = False
            logger.warning(
                "Skipping API Gateway v2 sync for account %s in region %s after transient GetApis failure: %s",
                current_aws_account_id,
                region,
                error,
            )
            continue
    if cleanup_safe:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping API Gateway v2 cleanup for account %s because one or more regions had transient API Gateway v2 failures. Preserving last-known-good API Gateway v2 state.",
            current_aws_account_id,
        )
