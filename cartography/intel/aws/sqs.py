import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import boto3
import neo4j
from botocore.exceptions import ClientError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.sqs.queue import SQSQueueSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_sqs_queue_list(boto3_session: boto3.session.Session, region: str) -> List[str]:
    client = boto3_session.client("sqs", region_name=region)
    paginator = client.get_paginator("list_queues")
    queues: List[Any] = []
    for page in paginator.paginate():
        queues.extend(page.get("QueueUrls", []))
    return queues


@timeit
@aws_handle_regions
def get_sqs_queue_attributes(
    boto3_session: boto3.session.Session,
    queue_urls: List[str],
) -> List[Tuple[str, Any]]:
    """Iterates over all SQS queues and returns a list of (url, attributes)."""
    client = boto3_session.client("sqs")

    queue_attributes = []
    for queue_url in queue_urls:
        try:
            response = client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["All"],
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AWS.SimpleQueueService.NonExistentQueue":
                logger.warning(
                    f"Failed to retrieve SQS queue {queue_url} - Queue does not exist error",
                )
                continue
            else:
                raise
        queue_attributes.append((queue_url, response["Attributes"]))

    return queue_attributes


def transform_sqs_queues(data: List[Tuple[str, Any]]) -> List[Dict[str, Any]]:
    transformed: List[Dict[str, Any]] = []
    for url, attrs in data:
        queue = dict(attrs)
        queue["url"] = url
        queue["name"] = attrs["QueueArn"].split(":")[-1]
        queue["CreatedTimestamp"] = int(attrs.get("CreatedTimestamp", 0))
        queue["LastModifiedTimestamp"] = int(attrs.get("LastModifiedTimestamp", 0))
        redrive_policy = attrs.get("RedrivePolicy")
        if redrive_policy:
            try:
                rp = json.loads(redrive_policy)
            except TypeError:
                rp = {}
            queue["redrive_policy_dead_letter_target_arn"] = rp.get(
                "deadLetterTargetArn"
            )
            queue["redrive_policy_max_receive_count"] = rp.get("maxReceiveCount")
        transformed.append(queue)
    return transformed


@timeit
def load_sqs_queues(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        SQSQueueSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup_sqs_queues(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SQSQueueSchema(), common_job_parameters).run(
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
            "Syncing SQS for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        queue_urls = get_sqs_queue_list(boto3_session, region)
        if not queue_urls:
            continue
        queue_attributes = get_sqs_queue_attributes(boto3_session, queue_urls)
        transformed = transform_sqs_queues(queue_attributes)
        load_sqs_queues(
            neo4j_session,
            transformed,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup_sqs_queues(neo4j_session, common_job_parameters)
