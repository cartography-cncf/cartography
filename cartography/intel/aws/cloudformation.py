import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.cloudformation import AWSCloudFormationStackSchema
from cartography.util import aws_handle_regions
from cartography.util import dict_date_to_epoch
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_stacks(boto3_session: boto3.Session, region: str) -> List[Dict[str, Any]]:
    client = boto3_session.client("cloudformation", region_name=region)
    stacks = []
    paginator = client.get_paginator("describe_stacks")
    for page in paginator.paginate():
        stacks.extend(page["Stacks"])
    return stacks


def transform_stacks(stacks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for stack in stacks:
        stack["CreationTime"] = dict_date_to_epoch(stack, "CreationTime")
        stack["LastUpdatedTime"] = dict_date_to_epoch(stack, "LastUpdatedTime")
    return stacks


@timeit
def load_stacks(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSCloudFormationStackSchema(),
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
    logger.info("Running AWS CloudFormation cleanup")
    GraphJob.from_node_schema(
        AWSCloudFormationStackSchema(), common_job_parameters
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
            f"Syncing AWS CloudFormation for region '{region}' in account '{current_aws_account_id}'."
        )

        stacks = get_stacks(boto3_session, region)
        stacks = transform_stacks(stacks)
        load_stacks(neo4j_session, stacks, region, current_aws_account_id, update_tag)

    cleanup(neo4j_session, common_job_parameters)
