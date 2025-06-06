import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.sns.topic import SNSTopicSchema
from cartography.models.aws.sns.topic_subscription import SNSTopicSubscriptionSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
@aws_handle_regions
def get_sns_topics(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    """
    Get all SNS Topics for a region.
    """
    client = boto3_session.client("sns", region_name=region)
    paginator = client.get_paginator("list_topics")
    topics = []
    for page in paginator.paginate():
        topics.extend(page.get("Topics", []))

    return topics


@timeit
def get_topic_attributes(
    boto3_session: boto3.session.Session, topic_arn: str, region: str
) -> Optional[Dict]:
    """
    Get attributes for an SNS Topic.
    """
    client = boto3_session.client("sns", region_name=region)
    try:
        return client.get_topic_attributes(TopicArn=topic_arn)
    except Exception as e:
        logger.warning(f"Error getting attributes for SNS topic {topic_arn}: {e}")
        return None


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
    logger.info(f"Loading {len(data)} SNS topics for region {region} into graph.")

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
    client = boto3_session.client("sns", region_name=region)
    paginator = client.get_paginator("list_subscriptions")
    subscriptions = []
    for page in paginator.paginate():
        subscriptions.extend(page.get("Subscriptions", []))

    return subscriptions


@timeit
@aws_handle_regions
def get_subscription_attributes(
    boto3_session: boto3.session.Session, region: str, subscription_arn: Any
) -> Dict[str, Any]:
    """
    Get all SNS  Subscriptions attributes for a region.
    """
    client = boto3_session.client("sns", region_name=region)
    response = client.get_subscription_attributes(SubscriptionArn=subscription_arn)
    return response.get("Attributes", {})


def transform_subscriptions(
    subscriptions: List[Dict], attributes: Dict[Any, Dict], region: str
) -> List[Dict]:
    """
    Transform SNS topic subscriptions data for ingestion
    """
    transformed_subscriptions = []
    for subscription in subscriptions:
        subscription_arn = subscription["SubscriptionArn"]

        # Get attributes
        subscription_attrs = attributes.get(subscription_arn, {}).get("Attributes", {})

        transformed_subscription = {
            "SubscriptionArn": subscription_arn,
            "TopicArn": subscription.get("TopicArn", ""),
            "ConfirmationWasAuthenticated": subscription_attrs.get(
                "ConfirmationWasAuthenticated", ""
            ),
            "DeliveryPolicy": subscription_attrs.get("DeliveryPolicy", ""),
            "EffectiveDeliveryPolicy": subscription_attrs.get(
                "EffectiveDeliveryPolicy", ""
            ),
            "FilterPolicy": subscription_attrs.get("FilterPolicy", ""),
            "FilterPolicyScope": subscription_attrs.get("FilterPolicyScope", ""),
            "Owner": subscription_attrs.get("Owner", ""),
            "PendingConfirmation": subscription_attrs.get("PendingConfirmation", ""),
            "RawMessageDelivery": subscription_attrs.get("RawMessageDelivery", ""),
            "RedrivePolicy": subscription_attrs.get("RedrivePolicy", ""),
            "SubscriptionRoleArn": subscription_attrs.get("SubscriptionRoleArn", ""),
        }

        transformed_subscriptions.append(transformed_subscription)

    return transformed_subscriptions


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

        topic_attributes = {}
        for topic in topics:
            topic_arn = topic["TopicArn"]
            attrs = get_topic_attributes(boto3_session, topic_arn, region)
            if attrs:
                topic_attributes[topic_arn] = attrs

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
        subscription_attributes = {}

        for subscription in subscriptions:
            subscription_arn = subscription.get("SubscriptionArn")

            attributes = get_subscription_attributes(
                boto3_session, region, subscription_arn
            )

            if attributes:
                subscription_attributes[subscription_arn] = attributes

        transformed_subscriptions = transform_subscriptions(
            subscriptions, subscription_attributes, region
        )

        load_sns_topic_subscription(
            neo4j_session,
            transformed_subscriptions,
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
        synced_type="SNSTopic",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
