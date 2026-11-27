import logging
from functools import wraps
from typing import Any
from typing import cast

import boto3
import neo4j
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import ReadTimeoutError
from botocore.exceptions import SSLError
from botocore.parsers import ResponseParserError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.eventbridge.schema_registry import (
    EventSchemasRegistrySchema,
)
from cartography.util import aws_handle_regions
from cartography.util import AWSGetFunc
from cartography.util import timeit

logger = logging.getLogger(__name__)


class EventSchemasTransientRegionFailure(Exception):
    pass


def _raise_on_transient_failure(func: AWSGetFunc) -> AWSGetFunc:
    # aws_handle_regions turns some 5xx and timeouts into [], which cleanup
    # can't tell apart from an empty region.
    @wraps(func)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except ClientError as error:
            status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if (status or 0) >= 500:
                raise EventSchemasTransientRegionFailure(func.__name__) from error
            raise
        except (
            ConnectTimeoutError,
            ReadTimeoutError,
            ResponseParserError,
            SSLError,
        ) as error:
            raise EventSchemasTransientRegionFailure(func.__name__) from error

    return cast(AWSGetFunc, wrapped)


@timeit
@aws_handle_regions
@_raise_on_transient_failure
def get_event_schema_registries(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    client = create_boto3_client(
        boto3_session,
        "schemas",
        region_name=region,
    )
    # AWS-managed registries like aws.events have no RegistryArn.
    paginator = client.get_paginator("list_registries")
    registries: list[dict[str, Any]] = []
    for page in paginator.paginate(Scope="LOCAL"):
        registries.extend(page.get("Registries", []))
    return registries


@timeit
def load_event_schema_registries(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        "Loading %d EventBridge schema registries for region '%s' into graph.",
        len(data),
        region,
    )
    load(
        neo4j_session,
        EventSchemasRegistrySchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Running EventBridge schema registry cleanup job.")
    GraphJob.from_node_schema(
        EventSchemasRegistrySchema(),
        common_job_parameters,
    ).run(neo4j_session)


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
            "Syncing EventBridge schema registries for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        try:
            registries = get_event_schema_registries(boto3_session, region)
        except EventSchemasTransientRegionFailure as error:
            cleanup_safe = False
            logger.warning(
                "Skipping EventBridge schema registries for account %s in region %s: %s",
                current_aws_account_id,
                region,
                error,
            )
            continue
        load_event_schema_registries(
            neo4j_session,
            registries,
            region,
            current_aws_account_id,
            update_tag,
        )
    if cleanup_safe:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping EventBridge schema registry cleanup for account %s to keep last-known-good data.",
            current_aws_account_id,
        )
