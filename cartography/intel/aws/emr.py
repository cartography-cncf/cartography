import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.models.aws.emr import EMRClusterSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

# ListClusters also returns clusters terminated in the last two months. Those no longer
# run anything, and describing each of them dominates the sync in accounts that launch
# short-lived clusters, so only clusters that can still run work are synced.
ACTIVE_CLUSTER_STATES = [
    "STARTING",
    "BOOTSTRAPPING",
    "RUNNING",
    "WAITING",
    "TERMINATING",
]


@timeit
@aws_handle_regions
def get_emr_clusters(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict[str, Any]]:
    client = create_boto3_client(
        boto3_session,
        "emr",
        region_name=region,
        config=get_botocore_config(),
    )
    paginator = client.get_paginator("list_clusters")
    return [
        cluster
        for page in paginator.paginate(ClusterStates=ACTIVE_CLUSTER_STATES)
        for cluster in page["Clusters"]
    ]


# Not wrapped in aws_handle_regions: a timeout while describing must fail the sync,
# not read as an empty region whose clusters cleanup would then delete.
@timeit
def get_emr_cluster_details(
    boto3_session: boto3.session.Session,
    region: str,
    clusters: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    client = create_boto3_client(
        boto3_session,
        "emr",
        region_name=region,
        config=get_botocore_config(),
    )
    cluster_data: List[Dict[str, Any]] = []
    for cluster in clusters:
        cluster_details = get_emr_describe_cluster(client, cluster["Id"])
        if cluster_details:
            cluster_data.append(cluster_details)
    return cluster_data


@timeit
def get_emr_describe_cluster(
    client: Any,
    cluster_id: str,
) -> Dict[str, Any]:
    cluster_details: Dict[str, Any] = {}
    try:
        response = client.describe_cluster(ClusterId=cluster_id)
        cluster_details = response["Cluster"]
    except botocore.exceptions.ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        logger.warning(
            f"Could not run EMR describe_cluster due to boto3 error {code}: {msg}. Skipping.",
        )
    return cluster_details


@timeit
def load_emr_clusters(
    neo4j_session: neo4j.Session,
    cluster_data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading EMR {len(cluster_data)} clusters for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        EMRClusterSchema(),
        cluster_data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Running EMR cleanup job.")
    cleanup_job = GraphJob.from_node_schema(EMRClusterSchema(), common_job_parameters)
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
            f"Syncing EMR for region '{region}' in account '{current_aws_account_id}'.",
        )

        clusters = get_emr_clusters(boto3_session, region)
        cluster_data = get_emr_cluster_details(boto3_session, region, clusters)

        load_emr_clusters(
            neo4j_session,
            cluster_data,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
