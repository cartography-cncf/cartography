import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.elasticache.cluster import ElasticacheClusterSchema
from cartography.models.aws.elasticache.topic import ElasticacheTopicSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
@aws_handle_regions
def get_elasticache_clusters(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    client = boto3_session.client("elasticache", region_name=region)
    paginator = client.get_paginator("describe_cache_clusters")
    clusters: list[dict[str, Any]] = []
    for page in paginator.paginate():
        clusters.extend(page.get("CacheClusters", []))
    return clusters


def transform_elasticache_clusters(
    clusters: list[dict[str, Any]], region: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cluster_data: list[dict[str, Any]] = []
    topics: dict[str, dict[str, Any]] = {}

    for cluster in clusters:
        notification = cluster.get("NotificationConfiguration", {})
        topic_arn = notification.get("TopicArn")
        cluster_record = {
            "ARN": cluster["ARN"],
            "CacheClusterId": cluster["CacheClusterId"],
            "CacheNodeType": cluster.get("CacheNodeType"),
            "Engine": cluster.get("Engine"),
            "EngineVersion": cluster.get("EngineVersion"),
            "CacheClusterStatus": cluster.get("CacheClusterStatus"),
            "NumCacheNodes": cluster.get("NumCacheNodes"),
            "PreferredAvailabilityZone": cluster.get("PreferredAvailabilityZone"),
            "PreferredMaintenanceWindow": cluster.get("PreferredMaintenanceWindow"),
            "CacheClusterCreateTime": cluster.get("CacheClusterCreateTime"),
            "CacheSubnetGroupName": cluster.get("CacheSubnetGroupName"),
            "AutoMinorVersionUpgrade": cluster.get("AutoMinorVersionUpgrade"),
            "ReplicationGroupId": cluster.get("ReplicationGroupId"),
            "SnapshotRetentionLimit": cluster.get("SnapshotRetentionLimit"),
            "SnapshotWindow": cluster.get("SnapshotWindow"),
            "AuthTokenEnabled": cluster.get("AuthTokenEnabled"),
            "TransitEncryptionEnabled": cluster.get("TransitEncryptionEnabled"),
            "AtRestEncryptionEnabled": cluster.get("AtRestEncryptionEnabled"),
            "TopicArn": topic_arn,
            "Region": region,
        }
        cluster_data.append(cluster_record)

        if topic_arn:
            topics.setdefault(
                topic_arn,
                {
                    "TopicArn": topic_arn,
                    "TopicStatus": notification.get("TopicStatus"),
                    "cluster_arns": [],
                },
            )["cluster_arns"].append(cluster["ARN"])

    return cluster_data, list(topics.values())


@timeit
def load_elasticache_clusters(
    neo4j_session: neo4j.Session,
    clusters: list[dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    logger.info(
        f"Loading {len(clusters)} ElastiCache clusters for region '{region}' into graph."
    )
    load(
        neo4j_session,
        ElasticacheClusterSchema(),
        clusters,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
    )


@timeit
def load_elasticache_topics(
    neo4j_session: neo4j.Session,
    topics: list[dict[str, Any]],
    aws_account_id: str,
    update_tag: int,
) -> None:
    if not topics:
        return
    logger.info(f"Loading {len(topics)} ElastiCache topics into graph.")
    load(
        neo4j_session,
        ElasticacheTopicSchema(),
        topics,
        lastupdated=update_tag,
        AWS_ID=aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(ElasticacheClusterSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ElasticacheTopicSchema(), common_job_parameters).run(
        neo4j_session
    )


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
            "Syncing ElastiCache clusters for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        raw_clusters = get_elasticache_clusters(boto3_session, region)
        cluster_data, topic_data = transform_elasticache_clusters(raw_clusters, region)
        load_elasticache_clusters(
            neo4j_session,
            cluster_data,
            region,
            current_aws_account_id,
            update_tag,
        )
        load_elasticache_topics(
            neo4j_session,
            topic_data,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="ElasticacheCluster",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
