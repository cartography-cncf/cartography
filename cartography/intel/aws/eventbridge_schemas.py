import json
import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.models.aws.eventbridge.schema_registry import (
    EventSchemasRegistrySchema,
)
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_event_schema_registries(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    client = create_boto3_client(
        boto3_session,
        "schemas",
        region_name=region,
        config=get_botocore_config(),
    )
    # Scope is omitted so both account registries and AWS-managed registries are returned.
    paginator = client.get_paginator("list_registries")
    registries: list[dict[str, Any]] = []
    for page in paginator.paginate():
        for summary in page.get("Registries", []):
            # ListRegistries does not return Description.
            registries.append(
                client.describe_registry(RegistryName=summary["RegistryName"]),
            )
    return registries


def transform_event_schema_registries(
    registries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for registry in registries:
        tags = registry.get("Tags")
        transformed.append(
            {
                "RegistryArn": registry["RegistryArn"],
                "RegistryName": registry["RegistryName"],
                "Description": registry.get("Description"),
                "Tags": json.dumps(tags) if tags is not None else None,
            },
        )
    return transformed


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
    for region in regions:
        logger.info(
            "Syncing EventBridge schema registries for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        registries = get_event_schema_registries(boto3_session, region)
        load_event_schema_registries(
            neo4j_session,
            transform_event_schema_registries(registries),
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
