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
from cartography.models.aws.cloudwatch.logmetricfilter import (
    CloudWatchLogMetricFilterSchema,
)
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_cloudwatch_log_groups(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "cloudwatch", region_name=region, config=get_botocore_config()
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
@aws_handle_regions
def get_cloudwatch_log_metric_filters(boto3_session: boto3.Session, region: str) -> List[Dict[str, Any]]:
    logs_client = boto3_session.client("logs", region_name=region, config=get_botocore_config())
    paginator = logs_client.get_paginator("describe_metric_filters")
    metric_filters = []

    for page in paginator.paginate():
        metric_filters.extend(page.get("metricFilters", []))

    return metric_filters

@timeit
def load_cloudwatch_log_metric_filters(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(data)} CloudWatch log metric filters for region '{region}'.")
    for mf in data:
        mf["id"] = f"{aws_account_id}-{region}-{mf['filterName']}"  # Unique ID

    load(
        neo4j_session,
        CloudWatchLogMetricFilterSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
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

    log_metric_filter_cleanup_job = GraphJob.from_node_schema(
        CloudWatchLogMetricFilterSchema(), common_job_parameters
    )
    log_metric_filter_cleanup_job.run(neo4j_session)

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

        filters = get_cloudwatch_log_metric_filters(boto3_session, region)

        load_cloudwatch_log_metric_filters(
            neo4j_session,
            filters,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
