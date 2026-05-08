import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.redshift import RedshiftClusterSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_redshift_cluster_data(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict]:
    client = create_boto3_client(boto3_session, "redshift", region_name=region)
    paginator = client.get_paginator("describe_clusters")
    clusters: list[dict] = []
    for page in paginator.paginate():
        clusters.extend(page["Clusters"])
    return clusters


def _make_redshift_cluster_arn(
    region: str,
    aws_account_id: str,
    cluster_identifier: str,
) -> str:
    """Cluster ARN format: https://docs.aws.amazon.com/redshift/latest/mgmt/redshift-iam-access-control-overview.html"""
    return f"arn:aws:redshift:{region}:{aws_account_id}:cluster:{cluster_identifier}"


def transform_redshift_cluster_data(
    clusters: list[dict],
    region: str,
    current_aws_account_id: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for cluster in clusters:
        cluster["arn"] = _make_redshift_cluster_arn(
            region,
            current_aws_account_id,
            cluster["ClusterIdentifier"],
        )
        cluster["ClusterCreateTime"] = (
            str(cluster["ClusterCreateTime"])
            if "ClusterCreateTime" in cluster
            else None
        )
        endpoint = cluster.get("Endpoint", {})
        cluster["_endpoint_address"] = endpoint.get("Address") if endpoint else None
        cluster["_endpoint_port"] = endpoint.get("Port") if endpoint else None
        cluster["_security_group_ids"] = [
            sg["VpcSecurityGroupId"] for sg in cluster.get("VpcSecurityGroups", [])
        ]
        cluster["_iam_role_arns"] = [
            role["IamRoleArn"] for role in cluster.get("IamRoles", [])
        ]
        result.append(cluster)
    return result


@timeit
def load_redshift_cluster_data(
    neo4j_session: neo4j.Session,
    clusters: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        RedshiftClusterSchema(),
        clusters,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(RedshiftClusterSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync_redshift_clusters(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    data = get_redshift_cluster_data(boto3_session, region)
    transformed = transform_redshift_cluster_data(data, region, current_aws_account_id)
    load_redshift_cluster_data(
        neo4j_session,
        transformed,
        region,
        current_aws_account_id,
        aws_update_tag,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    for region in regions:
        logger.info(
            "Syncing Redshift clusters for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        sync_redshift_clusters(
            neo4j_session,
            boto3_session,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
