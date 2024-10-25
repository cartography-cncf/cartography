import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import boto3
import neo4j
from botocore.exceptions import ClientError

from cartography.intel.aws.util.boto3 import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_sqs_queue_list(boto3_session: boto3.session.Session, region: str) -> List[str]:
    client = boto3_session.client('sqs', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('list_queues')
    queues: List[Any] = []
    for page in paginator.paginate():
        queues.extend(page.get('QueueUrls', []))
    return queues


@timeit
@aws_handle_regions
def get_sqs_queue_attributes(
        boto3_session: boto3.session.Session,
        queue_urls: List[str],
) -> List[Tuple[str, Any]]:
    """
    Iterates over all SQS queues. Returns a dict with url as key, and attributes as value.
    """
    client = boto3_session.client('sqs', config=get_botocore_config())

    queue_attributes = []
    for queue_url in queue_urls:
        try:
            response = client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['All'])
        except ClientError as e:
            if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
                logger.warning(f"Failed to retrieve SQS queue {queue_url} - Queue does not exist error")
                continue
            else:
                raise
        queue_attributes.append((queue_url, response['Attributes']))

    return queue_attributes


@timeit
def load_sqs_queues(
    neo4j_session: neo4j.Session,
    data: List[Tuple[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_queues = """
    UNWIND $Queues as sqs_queue
        MERGE (queue:SQSQueue{id: sqs_queue.QueueArn})
        ON CREATE SET queue.firstseen = timestamp(), queue.url = sqs_queue.url
        SET queue.name = sqs_queue.name, queue.region = $Region, queue.arn = sqs_queue.QueueArn,
            queue.created_timestamp = sqs_queue.CreatedTimestamp, queue.delay_seconds = sqs_queue.DelaySeconds,
            queue.last_modified_timestamp = sqs_queue.LastModifiedTimestamp,
            queue.maximum_message_size = sqs_queue.MaximumMessageSize,
            queue.message_retention_period = sqs_queue.MessageRetentionPeriod,
            queue.policy = sqs_queue.Policy, queue.arn = sqs_queue.QueueArn,
            queue.receive_message_wait_time_seconds = sqs_queue.ReceiveMessageWaitTimeSeconds,
            queue.redrive_policy_dead_letter_target_arn = sqs_queue.RedrivePolicy.deadLetterTargetArn,
            queue.redrive_policy_max_receive_count = sqs_queue.RedrivePolicy.maxReceiveCount,
            queue.visibility_timeout = sqs_queue.VisibilityTimeout,
            queue.kms_master_key_id = sqs_queue.KmsMasterKeyId,
            queue.kms_data_key_reuse_period_seconds = sqs_queue.KmsDataKeyReusePeriodSeconds,
            queue.fifo_queue = sqs_queue.FifoQueue,
            queue.content_based_deduplication = sqs_queue.ContentBasedDeduplication,
            queue.deduplication_scope = sqs_queue.DeduplicationScope,
            queue.fifo_throughput_limit = sqs_queue.FifoThroughputLimit,
            queue.lastupdated = $aws_update_tag
        WITH queue
        MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (owner)-[r:RESOURCE]->(queue)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """
    dead_letter_queues: List[Dict] = []
    queues: List[Dict] = []
    for url, queue in data:
        queue['url'] = url
        queue['name'] = queue['QueueArn'].split(':')[-1]
        queue['CreatedTimestamp'] = int(queue['CreatedTimestamp'])
        queue['LastModifiedTimestamp'] = int(queue['LastModifiedTimestamp'])
        redrive_policy = queue.get('RedrivePolicy')
        if redrive_policy:
            try:
                rp = json.loads(redrive_policy)
            except TypeError:
                rp = {}
            queue['RedrivePolicy'] = rp
            dead_letter_arn = rp.get('deadLetterTargetArn')
            if dead_letter_arn:
                dead_letter_queues.append({
                    'arn': queue['QueueArn'],
                    'dead_letter_arn': dead_letter_arn,
                })
        queues.append(queue)

    neo4j_session.run(
        ingest_queues,
        Queues=queues,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )

    _attach_dead_letter_queues(neo4j_session, dead_letter_queues, aws_update_tag)


@timeit
def _attach_dead_letter_queues(neo4j_session: neo4j.Session, data: List[Dict[str, str]], aws_update_tag: int) -> None:
    """
    Attach deadletter queues to their queues.
    """
    attach_deadletter_to_queue = """
    UNWIND $Relations as relation
        MATCH (queue:SQSQueue{id: relation.arn}), (deadletter:SQSQueue{id: relation.dead_letter_arn})
        MERGE (queue)-[r:HAS_DEADLETTER_QUEUE]->(deadletter)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """
    neo4j_session.run(
        attach_deadletter_to_queue,
        Relations=data,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_sqs_queues(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_sqs_queues_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing SQS for region '%s' in account '%s'.", region, current_aws_account_id)
        queue_urls = get_sqs_queue_list(boto3_session, region)
        if len(queue_urls) == 0:
            continue
        queue_attributes = get_sqs_queue_attributes(boto3_session, queue_urls)
        load_sqs_queues(neo4j_session, queue_attributes, region, current_aws_account_id, update_tag)
    cleanup_sqs_queues(neo4j_session, common_job_parameters)
