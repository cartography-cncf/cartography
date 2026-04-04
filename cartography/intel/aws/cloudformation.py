import json
import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.models.aws.cloudformation.stack import CloudFormationStackSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
@aws_handle_regions
def get_cloudformation_stacks(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    client = boto3_session.client(
        "cloudformation",
        region_name=region,
        config=get_botocore_config(),
    )
    stacks: list[dict[str, Any]] = []
    paginator = client.get_paginator("describe_stacks")
    for page in paginator.paginate():
        stacks.extend(page["Stacks"])
    return stacks


def transform_cloudformation_stacks(
    stacks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    for stack in stacks:
        if stack.get("Tags") is not None:
            stack["Tags"] = json.dumps(stack["Tags"])
    return stacks


@timeit
def load_cloudformation_stacks(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        "Loading %d CloudFormation stacks for region '%s' into graph.",
        len(data),
        region,
    )
    load(
        neo4j_session,
        CloudFormationStackSchema(),
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
    logger.debug("Running CloudFormation cleanup job.")
    GraphJob.from_node_schema(
        CloudFormationStackSchema(),
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
            "Syncing CloudFormation stacks for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        raw_stacks = get_cloudformation_stacks(boto3_session, region)
        stacks = transform_cloudformation_stacks(raw_stacks)
        load_cloudformation_stacks(
            neo4j_session,
            stacks,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="CloudFormationStack",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
