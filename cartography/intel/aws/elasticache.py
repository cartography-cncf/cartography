import logging
from typing import Dict
from typing import List
from typing import Set

import boto3
import neo4j

from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


def _get_topic(cluster: Dict) -> Dict:
    return cluster["NotificationConfiguration"]


def transform_elasticache_topics(cluster_data: List[Dict]) -> List[Dict]:
    """
    Collect unique TopicArns from the cluster data
    """
    seen: Set[str] = set()
    topics: List[Dict] = []
    for cluster in cluster_data:
        topic = _get_topic(cluster)
        topic_arn = topic["TopicArn"]
        if topic_arn not in seen:
            seen.add(topic_arn)
            topics.append(topic)
    return topics


@timeit
@aws_handle_regions
def get_elasticache_clusters(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
    logger.debug(f"Getting ElastiCache Clusters in region '{region}'.")
    client = boto3_session.client("elasticache", region_name=region)
    paginator = client.get_paginator("describe_cache_clusters")
    clusters: List[Dict] = []
    for page in paginator.paginate():
        clusters.extend(page["CacheClusters"])
    return clusters


@timeit
def load_elasticache_clusters(
    neo4j_session: neo4j.Session,
    clusters: List[Dict],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    query = """
    UNWIND $clusters as elasticache_cluster
        MERGE (cluster:ElasticacheCluster{id:elasticache_cluster.ARN})
        ON CREATE SET cluster.firstseen = timestamp(),
            cluster.arn = elasticache_cluster.ARN,
            cluster.topic_arn = elasticache_cluster.NotificationConfiguration.TopicArn,
            cluster.id = elasticache_cluster.CacheClusterId,
            cluster.region = $region
        SET cluster.lastupdated = $aws_update_tag

        WITH cluster, elasticache_cluster
        MATCH (owner:AWSAccount{id: $aws_account_id})
        MERGE (owner)-[r3:RESOURCE]->(cluster)
        ON CREATE SET r3.firstseen = timestamp()
        SET r3.lastupdated = $aws_update_tag

        WITH elasticache_cluster, owner
        WHERE NOT elasticache_cluster.NotificationConfiguration IS NULL
        MERGE (topic:ElasticacheTopic{id: elasticache_cluster.NotificationConfiguration.TopicArn})
        ON CREATE SET topic.firstseen = timestamp(),
            topic.arn = elasticache_cluster.NotificationConfiguration.TopicArn
        SET topic.lastupdated = $aws_update_tag,
            topic.status = elasticache_cluster.NotificationConfiguration.Status

        MERGE (topic)-[r:CACHE_CLUSTER]->(cluster)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
        WITH cluster, topic

        MERGE (owner)-[r2:RESOURCE]->(topic)
        ON CREATE SET r2.firstseen = timestamp()
        SET r2.lastupdated = $aws_update_tag
    """
    logger.info(
        f"Loading f{len(clusters)} ElastiCache clusters for region '{region}' into graph.",
    )
    neo4j_session.run(
        query,
        clusters=clusters,
        region=region,
        aws_update_tag=update_tag,
        aws_account_id=aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    run_cleanup_job(
        "aws_import_elasticache_cleanup.json",
        neo4j_session,
        {"UPDATE_TAG": update_tag, "AWS_ID": current_aws_account_id},
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info(
            f"Syncing ElastiCache clusters for region '{region}' in account {current_aws_account_id}",
        )
        clusters = get_elasticache_clusters(boto3_session, region)
        load_elasticache_clusters(
            neo4j_session,
            clusters,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, current_aws_account_id, update_tag)
    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="ElasticacheCluster",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
