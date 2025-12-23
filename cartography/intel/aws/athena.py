import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.athena import AWSAthenaWorkGroupSchema
from cartography.util import aws_handle_regions
from cartography.util import dict_date_to_epoch
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_work_groups(boto3_session: boto3.Session, region: str) -> List[Dict[str, Any]]:
    client = boto3_session.client("athena", region_name=region)
    work_groups = []
    paginator = client.get_paginator("list_work_groups")
    for page in paginator.paginate():
        work_groups.extend(page["WorkGroups"])
    return work_groups


def transform_work_groups(work_groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for wg in work_groups:
        wg["CreationTime"] = dict_date_to_epoch(wg, "CreationTime")
    return work_groups


@timeit
def load_work_groups(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSAthenaWorkGroupSchema(),
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
    logger.info("Running AWS Athena cleanup")
    GraphJob.from_node_schema(AWSAthenaWorkGroupSchema(), common_job_parameters).run(
        neo4j_session
    )


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
            f"Syncing AWS Athena for region '{region}' in account '{current_aws_account_id}'."
        )

        work_groups = get_work_groups(boto3_session, region)
        work_groups = transform_work_groups(work_groups)
        load_work_groups(
            neo4j_session, work_groups, region, current_aws_account_id, update_tag
        )

    cleanup(neo4j_session, common_job_parameters)
