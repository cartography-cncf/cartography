import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import boto3
import botocore.client
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.models.aws.sns.topic import SNSTopicSchema
from cartography.models.aws.sns.topic_subscription import SNSTopicSubscriptionSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import is_throttling_exception
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit
from cartography.util import to_asynchronous
from cartography.util import to_synchronous

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

# Bounds the GetTopicAttributes calls in flight per region. The account shares
# this quota with its own workloads, and it is as low as 30 TPS in some regions.
TOPIC_ATTRIBUTES_BATCH_SIZE = 10


@timeit
@aws_handle_regions
def get_sns_topics(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    """
    Get all SNS Topics for a region.
    """
    client = create_boto3_client(boto3_session, "sns", region_name=region)
    paginator = client.get_paginator("list_topics")
    topics = []
    for page in paginator.paginate():
        topics.extend(page.get("Topics", []))

    return topics


@timeit
def get_topic_attributes(
    client: botocore.client.BaseClient, topic_arn: str
) -> Optional[Dict]:
    """
    Get attributes for an SNS Topic.
    """
    try:
        return client.get_topic_attributes(TopicArn=topic_arn)
    except Exception as e:
        # to_asynchronous backs off and retries throttled calls, so let them
        # through rather than load the topic without its attributes.
        if is_throttling_exception(e):
            raise
        logger.warning(f"Error getting attributes for SNS topic {topic_arn}: {e}")
        return None


@timeit
def get_topics_attributes(
    boto3_session: boto3.session.Session, topics: List[Dict], region: str
) -> Dict[str, Dict]:
    """
    Get attributes for SNS Topics, keyed by topic ARN. Topics whose attributes
    could not be fetched are omitted.
    """
    # One shared client reuses its connection pool. A client per topic opens a
    # new TLS connection for every call.
    client = create_boto3_client(
        boto3_session,
        "sns",
        region_name=region,
        config=get_botocore_config(max_pool_connections=TOPIC_ATTRIBUTES_BATCH_SIZE),
    )

    async def _get_attributes(topic_arn: str) -> Optional[Dict]:
        return await to_asynchronous(get_topic_attributes, client, topic_arn)

    topic_arns = [topic["TopicArn"] for topic in topics]
    topic_attributes: Dict[str, Dict] = {}
    for i in range(0, len(topic_arns), TOPIC_ATTRIBUTES_BATCH_SIZE):
        batch = topic_arns[i : i + TOPIC_ATTRIBUTES_BATCH_SIZE]
        results = to_synchronous(*[_get_attributes(arn) for arn in batch])
        topic_attributes.update(
            {arn: attrs for arn, attrs in zip(batch, results) if attrs},
        )
    return topic_attributes


def transform_sns_topics(
    topics: List[Dict], attributes: Dict[str, Dict], region: str
) -> List[Dict]:
    """
    Transform SNS topic data for ingestion
    """
    transformed_topics = []
    for topic in topics:
        topic_arn = topic["TopicArn"]

        # Extract topic name from ARN
        # Format: arn:aws:sns:region:account-id:topic-name
        topic_name = topic_arn.split(":")[-1]

        # Get attributes
        topic_attrs = attributes.get(topic_arn, {}).get("Attributes", {})

        transformed_topic = {
            "TopicArn": topic_arn,
            "TopicName": topic_name,
            "DisplayName": topic_attrs.get("DisplayName", ""),
            "Owner": topic_attrs.get("Owner", ""),
            "SubscriptionsPending": int(topic_attrs.get("SubscriptionsPending", "0")),
            "SubscriptionsConfirmed": int(
                topic_attrs.get("SubscriptionsConfirmed", "0")
            ),
            "SubscriptionsDeleted": int(topic_attrs.get("SubscriptionsDeleted", "0")),
            "DeliveryPolicy": topic_attrs.get("DeliveryPolicy", ""),
            "EffectiveDeliveryPolicy": topic_attrs.get("EffectiveDeliveryPolicy", ""),
            "KmsMasterKeyId": topic_attrs.get("KmsMasterKeyId", ""),
        }

        transformed_topics.append(transformed_topic)

    return transformed_topics


@timeit
def load_sns_topics(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load SNS Topics information into the graph
    """
    load(
        neo4j_session,
        SNSTopicSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
    )


@timeit
@aws_handle_regions
def get_subscriptions(
    boto3_session: boto3.session.Session, region: str
) -> List[Dict[str, Any]]:
    """
    Get all SNS Topics Subscriptions for a region.
    """
    client = create_boto3_client(boto3_session, "sns", region_name=region)
    paginator = client.get_paginator("list_subscriptions")
    subscriptions = []
    for page in paginator.paginate():
        subscriptions.extend(page.get("Subscriptions", []))

    return subscriptions


@timeit
def load_sns_topic_subscription(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load SNS Topic Subscription information into the graph
    """
    logger.info(
        f"Loading {len(data)} SNS topic subscription for region {region} into graph."
    )

    load(
        neo4j_session,
        SNSTopicSubscriptionSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
    )


@timeit
def cleanup_sns(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """
    Run SNS cleanup job
    """
    logger.debug("Running SNS cleanup job.")
    cleanup_job = GraphJob.from_node_schema(SNSTopicSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)

    cleanup_job = GraphJob.from_node_schema(
        SNSTopicSubscriptionSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync SNS Topics and Subscriptions for all regions
    """
    for region in regions:
        logger.info(
            f"Syncing SNS Topics for {region} in account {current_aws_account_id}"
        )
        topics = get_sns_topics(boto3_session, region)

        topic_attributes = get_topics_attributes(boto3_session, topics, region)
        transformed_topics = transform_sns_topics(topics, topic_attributes, region)

        load_sns_topics(
            neo4j_session,
            transformed_topics,
            region,
            current_aws_account_id,
            update_tag,
        )

        # Get and load subscriptions
        subscriptions = get_subscriptions(boto3_session, region)

        load_sns_topic_subscription(
            neo4j_session,
            subscriptions,
            region,
            current_aws_account_id,
            update_tag,
        )

    # Cleanup and metadata update (outside region loop)
    cleanup_sns(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="AWSSNSTopic",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
