import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.cloudwatch.loggroup import CloudWatchLogGroupSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_cloudwatch_log_groups(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "logs", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("describe_log_groups")
    logGroups = []
    for page in paginator.paginate():
        logGroups.extend(page["logGroups"])
    return logGroups


@timeit
def load_cloudwatch_log_groups(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading CloudWatch {len(data)} log groups for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        CloudWatchLogGroupSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Running CloudWatch cleanup job.")
    cleanup_job = GraphJob.from_node_schema(
        CloudWatchLogGroupSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)


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
            f"Syncing CloudWatch for region '{region}' in account '{current_aws_account_id}'.",
        )
        logGroups = get_cloudwatch_log_groups(boto3_session, region)
        group_data: List[Dict[str, Any]] = []
        for logGroup in logGroups:
            group_data.append(logGroup)

        load_cloudwatch_log_groups(
            neo4j_session,
            group_data,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
