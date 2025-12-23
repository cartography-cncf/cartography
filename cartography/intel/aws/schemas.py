import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.eventbridge import AWSEventSchemasRegistrySchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_registries(boto3_session: boto3.Session, region: str) -> List[Dict[str, Any]]:
    client = boto3_session.client("schemas", region_name=region)
    registries = []
    paginator = client.get_paginator("list_registries")
    for page in paginator.paginate():
        registries.extend(page["Registries"])
    return registries


def transform_registries(registries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return registries


@timeit
def load_registries(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSEventSchemasRegistrySchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.info("Running AWS Schemas cleanup")
    GraphJob.from_node_schema(
        AWSEventSchemasRegistrySchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            f"Syncing AWS Event Schemas for region '{region}' in account '{current_aws_account_id}'."
        )

        registries = get_registries(boto3_session, region)
        registries = transform_registries(registries)
        load_registries(
            neo4j_session, registries, region, current_aws_account_id, update_tag
        )

    cleanup(neo4j_session, common_job_parameters)
