import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.cloudwatch.log_metric_filter import (
    CloudWatchLogMetricFilterSchema,
)
from cartography.models.aws.cloudwatch.loggroup import CloudWatchLogGroupSchema
from cartography.models.aws.cloudwatch.metric_alarm import CloudWatchMetricAlarmSchema
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
@aws_handle_regions
def get_cloudwatch_log_metric_filters(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    logs_client = boto3_session.client(
        "logs", region_name=region, config=get_botocore_config()
    )
    paginator = logs_client.get_paginator("describe_metric_filters")
    metric_filters = []

    for page in paginator.paginate():
        metric_filters.extend(page.get("metricFilters", []))

    return metric_filters


def transform_metric_filters(
    metric_filters: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    """
    Transform CloudWatch log metric filter data for ingestion into Neo4j.
    Ensures that the 'id' field is a unique combination of logGroupName and filterName.
    """
    transformed_filters = []
    for filter in metric_filters:
        transformed_filter = {
            "id": f"{filter['logGroupName']}:{filter['filterName']}",
            "arn": f"{filter['logGroupName']}:{filter['filterName']}",
            "filterName": filter["filterName"],
            "filterPattern": filter.get("filterPattern"),
            "logGroupName": filter["logGroupName"],
            "metricName": filter["metricTransformations"][0]["metricName"],
            "metricNamespace": filter["metricTransformations"][0]["metricNamespace"],
            "metricValue": filter["metricTransformations"][0]["metricValue"],
            "Region": region,
        }
        transformed_filters.append(transformed_filter)
    return transformed_filters


@timeit
@aws_handle_regions
def get_cloudwatch_metric_alarms(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "cloudwatch", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("describe_alarms")
    alarms = []
    for page in paginator.paginate():
        alarms.extend(page["MetricAlarms"])
    return alarms


def transform_metric_alarms(
    metric_alarms: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    """
    Transform CloudWatch metric alarm data for ingestion into Neo4j.
    """
    transformed_alarms = []
    for alarm in metric_alarms:
        transformed_alarm = {
            "AlarmArn": alarm["AlarmArn"],
            "AlarmName": alarm.get("AlarmName"),
            "AlarmDescription": alarm.get("AlarmDescription"),
            "StateValue": alarm.get("StateValue"),
            "StateReason": alarm.get("StateReason"),
            "ActionsEnabled": alarm.get("ActionsEnabled"),
            "ComparisonOperator": alarm.get("ComparisonOperator"),
            "Region": region,
        }
        transformed_alarms.append(transformed_alarm)
    return transformed_alarms


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
def load_cloudwatch_log_metric_filters(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading CloudWatch {len(data)} log metric filters for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        CloudWatchLogMetricFilterSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_cloudwatch_metric_alarms(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading CloudWatch {len(data)} metric alarms for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        CloudWatchMetricAlarmSchema(),
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
    GraphJob.from_node_schema(
        CloudWatchLogMetricFilterSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(CloudWatchMetricAlarmSchema(), common_job_parameters).run(
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
            f"Syncing CloudWatch for region '{region}' in account '{current_aws_account_id}'.",
        )
        logGroups = get_cloudwatch_log_groups(boto3_session, region)

        load_cloudwatch_log_groups(
            neo4j_session,
            logGroups,
            region,
            current_aws_account_id,
            update_tag,
        )

        metric_filters = get_cloudwatch_log_metric_filters(boto3_session, region)
        transformed_filters = transform_metric_filters(metric_filters, region)
        load_cloudwatch_log_metric_filters(
            neo4j_session,
            transformed_filters,
            region,
            current_aws_account_id,
            update_tag,
        )

        metric_alarms = get_cloudwatch_metric_alarms(boto3_session, region)
        transformed_alarms = transform_metric_alarms(metric_alarms, region)
        load_cloudwatch_metric_alarms(
            neo4j_session,
            transformed_alarms,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
