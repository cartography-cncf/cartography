import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import run_write_query
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_redshift_cluster_data(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
    client = boto3_session.client("redshift", region_name=region)
    paginator = client.get_paginator("describe_clusters")
    clusters: List[Dict] = []
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
    clusters: List[Dict],
    region: str,
    current_aws_account_id: str,
) -> None:
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


@timeit
def load_redshift_cluster_data(
    neo4j_session: neo4j.Session,
    clusters: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_cluster = """
    MERGE (cluster:RedshiftCluster{id: $Arn})
    ON CREATE SET cluster.firstseen = timestamp(),
    cluster.arn = $Arn
    SET cluster.availability_zone = $AZ,
    cluster.cluster_create_time = $ClusterCreateTime,
    cluster.cluster_identifier = $ClusterIdentifier,
    cluster.cluster_revision_number = $ClusterRevisionNumber,
    cluster.db_name = $DBName,
    cluster.encrypted = $Encrypted,
    cluster.cluster_status = $ClusterStatus,
    cluster.endpoint_address = $EndpointAddress,
    cluster.endpoint_port = $EndpointPort,
    cluster.master_username = $MasterUsername,
    cluster.node_type = $NodeType,
    cluster.number_of_nodes = $NumberOfNodes,
    cluster.publicly_accessible = $PubliclyAccessible,
    cluster.vpc_id = $VpcId,
    cluster.lastupdated = $aws_update_tag,
    cluster.region = $Region
    WITH cluster
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(cluster)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """
    for cluster in clusters:
        run_write_query(
            neo4j_session,
            ingest_cluster,
            Arn=cluster["arn"],
            AZ=cluster["AvailabilityZone"],
            ClusterCreateTime=cluster["ClusterCreateTime"],
            ClusterIdentifier=cluster["ClusterIdentifier"],
            ClusterRevisionNumber=cluster["ClusterRevisionNumber"],
            ClusterStatus=cluster["ClusterStatus"],
            DBName=cluster["DBName"],
            Encrypted=cluster["Encrypted"],
            EndpointAddress=cluster.get("Endpoint").get("Address"),  # type: ignore
            EndpointPort=cluster.get("Endpoint").get("Port"),  # type: ignore
            MasterUsername=cluster["MasterUsername"],
            NodeType=cluster["NodeType"],
            NumberOfNodes=cluster["NumberOfNodes"],
            PubliclyAccessible=cluster["PubliclyAccessible"],
            VpcId=cluster.get("VpcId"),
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )
        _attach_ec2_security_groups(neo4j_session, cluster, aws_update_tag)
        _attach_iam_roles(neo4j_session, cluster, aws_update_tag)
        _attach_aws_vpc(neo4j_session, cluster, aws_update_tag)


@timeit
def _attach_ec2_security_groups(
    neo4j_session: neo4j.Session,
    cluster: Dict,
    aws_update_tag: int,
) -> None:
    attach_cluster_to_group = """
    MATCH (c:RedshiftCluster{id:$ClusterArn})
    MERGE (sg:EC2SecurityGroup{id:$GroupId})
    MERGE (c)-[m:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
    ON CREATE SET m.firstseen = timestamp()
    SET m.lastupdated = $aws_update_tag
    """
    for group in cluster.get("VpcSecurityGroups", []):
        run_write_query(
            neo4j_session,
            attach_cluster_to_group,
            ClusterArn=cluster["arn"],
            GroupId=group["VpcSecurityGroupId"],
            aws_update_tag=aws_update_tag,
        )


@timeit
def _attach_iam_roles(
    neo4j_session: neo4j.Session,
    cluster: Dict,
    aws_update_tag: int,
) -> None:
    attach_cluster_to_role = """
    MATCH (c:RedshiftCluster{id:$ClusterArn})
    MERGE (p:AWSPrincipal{arn:$RoleArn})
    MERGE (c)-[s:STS_ASSUMEROLE_ALLOW]->(p)
    ON CREATE SET s.firstseen = timestamp()
    SET s.lastupdated = $aws_update_tag
    """
    for role in cluster.get("IamRoles", []):
        run_write_query(
            neo4j_session,
            attach_cluster_to_role,
            ClusterArn=cluster["arn"],
            RoleArn=role["IamRoleArn"],
            aws_update_tag=aws_update_tag,
        )


@timeit
def _attach_aws_vpc(
    neo4j_session: neo4j.Session,
    cluster: Dict,
    aws_update_tag: int,
) -> None:
    attach_cluster_to_vpc = """
    MATCH (c:RedshiftCluster{id:$ClusterArn})
    MERGE (v:AWSVpc{id:$VpcId})
    MERGE (c)-[m:MEMBER_OF_AWS_VPC]->(v)
    ON CREATE SET m.firstseen = timestamp()
    SET m.lastupdated = $aws_update_tag
    """
    if cluster.get("VpcId"):
        run_write_query(
            neo4j_session,
            attach_cluster_to_vpc,
            ClusterArn=cluster["arn"],
            VpcId=cluster["VpcId"],
            aws_update_tag=aws_update_tag,
        )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        "aws_import_redshift_clusters_cleanup.json",
        neo4j_session,
        common_job_parameters,
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
    transform_redshift_cluster_data(data, region, current_aws_account_id)
    load_redshift_cluster_data(
        neo4j_session,
        data,
        region,
        current_aws_account_id,
        aws_update_tag,
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
