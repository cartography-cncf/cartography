import logging
import time
from typing import Dict
from typing import List
from typing import Set

import boto3
import neo4j
from cloudconsolelink.clouds.aws import AWSLinker

from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)
aws_console_link = AWSLinker()


def _get_topic(cluster: Dict) -> Dict:
    return cluster['NotificationConfiguration']


def transform_elasticache_topics(cluster_data: List[Dict]) -> List[Dict]:
    """
    Collect unique TopicArns from the cluster data
    """
    seen: Set[str] = set()
    topics: List[Dict] = []
    for cluster in cluster_data:
        topic = _get_topic(cluster)
        topic_arn = topic['TopicArn']
        if topic_arn not in seen:
            seen.add(topic_arn)
            topics.append(topic)
    return topics


@timeit
@aws_handle_regions
def get_elasticache_clusters(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    logger.debug(f"Getting ElastiCache Clusters in region '{region}'.")
    client = boto3_session.client('elasticache', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_cache_clusters')
    clusters: List[Dict] = []
    for page in paginator.paginate():
        clusters.extend(page['CacheClusters'])
    for cluster in clusters:
        cluster['region'] = region
        cluster['consolelink'] = aws_console_link.get_console_link(arn=cluster['ARN'])
    return clusters


@timeit
def load_elasticache_clusters(
    neo4j_session: neo4j.Session, clusters: List[Dict],
    aws_account_id: str, update_tag: int,
) -> None:
    query = """
    UNWIND $clusters as elasticache_cluster
        MERGE (cluster:ElasticacheCluster{id:elasticache_cluster.ARN})
        ON CREATE SET cluster.firstseen = timestamp(),
            cluster.arn = elasticache_cluster.ARN,
            cluster.topic_arn = elasticache_cluster.NotificationConfiguration.TopicArn,
            cluster.cache_cluster_id = elasticache_cluster.CacheClusterId,
            cluster.region = elasticache_cluster.region
        SET cluster.lastupdated = $aws_update_tag,
            cluster.consolelink = elasticache_cluster.consolelink

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
    logger.info(f"Loading f{len(clusters)} ElastiCache clusters into graph.")
    neo4j_session.run(
        query,
        clusters=clusters,
        aws_update_tag=update_tag,
        aws_account_id=aws_account_id,
    )


@timeit
def attach_elasticache_clusters_to_security_groups(neo4j_session: neo4j.Session, clusters: List[Dict], update_tag: int) -> None:
    query = """
    UNWIND $clusters as elasticache_cluster
        MATCH (cluster:ElasticacheCluster{id:elasticache_cluster.ARN})
        UNWIND elasticache_cluster.SecurityGroups as sg
            MERGE (security_group:EC2SecurityGroup{id: sg.SecurityGroupId})
            ON CREATE SET security_group.firstseen = timestamp()
            SET security_group.lastupdated = $aws_update_tag
            WITH security_group, cluster
            MERGE (security_group)<-[r:MEMBER_OF_EC2_SECURITY_GROUP]-(cluster)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $aws_update_tag
    """
    neo4j_session.run(
        query,
        clusters=clusters,
        aws_update_tag=update_tag,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'aws_import_elasticache_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing ElastiCache for account '%s', at %s.", current_aws_account_id, tic)

    clusters = []
    for region in regions:
        logger.info(f"Syncing ElastiCache clusters for region '{region}' in account {current_aws_account_id}")
        clusters.extend(get_elasticache_clusters(boto3_session, region))

    logger.info(f"Total Elasticache Clusters: {len(clusters)}")

    load_elasticache_clusters(neo4j_session, clusters, current_aws_account_id, update_tag)
    attach_elasticache_clusters_to_security_groups(neo4j_session, clusters, update_tag)
    cleanup(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process ElastiCache: {toc - tic:0.4f} seconds")
