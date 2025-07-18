import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.models.aws.rds.cluster import RDSClusterSchema
from cartography.models.aws.rds.instance import RDSInstanceSchema
from cartography.models.aws.rds.snapshot import RDSSnapshotSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import aws_paginate
from cartography.util import dict_value_to_str
from cartography.util import merge_module_sync_metadata
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
@aws_handle_regions
def get_rds_cluster_data(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Any]:
    """
    Create an RDS boto3 client and grab all the DBClusters.
    """
    client = boto3_session.client("rds", region_name=region)
    paginator = client.get_paginator("describe_db_clusters")
    instances: List[Any] = []
    for page in paginator.paginate():
        instances.extend(page["DBClusters"])

    return instances


@timeit
def load_rds_clusters(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Ingest the RDS clusters to neo4j and link them to necessary nodes.
    """
    for cluster in data:
        cluster["EarliestRestorableTime"] = dict_value_to_str(
            cluster,
            "EarliestRestorableTime",
        )
        cluster["LatestRestorableTime"] = dict_value_to_str(
            cluster,
            "LatestRestorableTime",
        )
        cluster["ClusterCreateTime"] = dict_value_to_str(cluster, "ClusterCreateTime")
        cluster["EarliestBacktrackTime"] = dict_value_to_str(
            cluster,
            "EarliestBacktrackTime",
        )
        cluster["ScalingConfigurationInfoMinCapacity"] = cluster.get(
            "ScalingConfigurationInfo",
            {},
        ).get("MinCapacity")
        cluster["ScalingConfigurationInfoMaxCapacity"] = cluster.get(
            "ScalingConfigurationInfo",
            {},
        ).get("MaxCapacity")
        cluster["ScalingConfigurationInfoAutoPause"] = cluster.get(
            "ScalingConfigurationInfo",
            {},
        ).get("AutoPause")

    load(
        neo4j_session,
        RDSClusterSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
@aws_handle_regions
def get_rds_instance_data(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Any]:
    """
    Create an RDS boto3 client and grab all the DBInstances.
    """
    client = boto3_session.client("rds", region_name=region)
    paginator = client.get_paginator("describe_db_instances")
    instances: List[Any] = []
    for page in paginator.paginate():
        instances.extend(page["DBInstances"])

    return instances


@timeit
def load_rds_instances(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Ingest the RDS instances to Neo4j and link them to necessary nodes.
    """
    read_replicas = []
    clusters = []
    subnets = []

    for rds in data:
        if rds.get("ReadReplicaSourceDBInstanceIdentifier"):
            read_replicas.append(rds)

        if rds.get("DBClusterIdentifier"):
            clusters.append(rds)

        if rds.get("DBSubnetGroup"):
            subnets.append(rds)

    load(
        neo4j_session,
        RDSInstanceSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )

    _attach_ec2_subnet_groups(
        neo4j_session,
        subnets,
        region,
        current_aws_account_id,
        aws_update_tag,
    )
    _attach_read_replicas(neo4j_session, read_replicas, aws_update_tag)
    _attach_clusters(neo4j_session, clusters, aws_update_tag)


@timeit
@aws_handle_regions
def get_rds_snapshot_data(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Any]:
    """
    Create an RDS boto3 client and grab all the DBSnapshots.
    """
    client = boto3_session.client("rds", region_name=region)
    snapshots = list(aws_paginate(client, "describe_db_snapshots", "DBSnapshots"))
    return snapshots


@timeit
def load_rds_snapshots(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Ingest the RDS snapshots to neo4j and link them to necessary nodes.
    """
    load(
        neo4j_session,
        RDSSnapshotSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def _attach_ec2_subnet_groups(
    neo4j_session: neo4j.Session,
    instances: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Attach RDS instances to their EC2 subnet groups
    """
    attach_rds_to_subnet_group = """
    UNWIND $SubnetGroups as rds_sng
        MERGE (sng:DBSubnetGroup{id: rds_sng.arn})
        ON CREATE SET sng.firstseen = timestamp()
        SET sng.name = rds_sng.DBSubnetGroupName,
            sng.vpc_id = rds_sng.VpcId,
            sng.description = rds_sng.DBSubnetGroupDescription,
            sng.status = rds_sng.DBSubnetGroupStatus,
            sng.lastupdated = $aws_update_tag
        WITH sng, rds_sng.instance_arn AS instance_arn
        MATCH(rds:RDSInstance{id: instance_arn})
        MERGE(rds)-[r:MEMBER_OF_DB_SUBNET_GROUP]->(sng)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """
    db_sngs = []
    for instance in instances:
        db_sng = instance["DBSubnetGroup"]
        db_sng["arn"] = _get_db_subnet_group_arn(
            region,
            current_aws_account_id,
            db_sng["DBSubnetGroupName"],
        )
        db_sng["instance_arn"] = instance["DBInstanceArn"]
        db_sngs.append(db_sng)
    neo4j_session.run(
        attach_rds_to_subnet_group,
        SubnetGroups=db_sngs,
        aws_update_tag=aws_update_tag,
    )
    _attach_ec2_subnets_to_subnetgroup(
        neo4j_session,
        db_sngs,
        region,
        current_aws_account_id,
        aws_update_tag,
    )


@timeit
def _attach_ec2_subnets_to_subnetgroup(
    neo4j_session: neo4j.Session,
    db_subnet_groups: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Attach EC2Subnets to their DB Subnet Group.

    From https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html:
    `Each DB subnet group should have subnets in at least two Availability Zones in a given region. When creating a DB
    instance in a VPC, you must select a DB subnet group. Amazon RDS uses that DB subnet group and your preferred
    Availability Zone to select a subnet and an IP address within that subnet to associate with your DB instance.`
    """
    attach_subnets_to_sng = """
    UNWIND $Subnets as rds_sn
        MATCH(sng:DBSubnetGroup{id: rds_sn.sng_arn})
        MERGE(subnet:EC2Subnet{subnetid: rds_sn.sn_id})
        ON CREATE SET subnet.firstseen = timestamp()
        MERGE(sng)-[r:RESOURCE]->(subnet)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag,
        subnet.availability_zone = rds_sn.az,
        subnet.lastupdated = $aws_update_tag
    """
    subnets = []
    for subnet_group in db_subnet_groups:
        for subnet in subnet_group.get("Subnets", []):
            sn_id = subnet.get("SubnetIdentifier")
            sng_arn = _get_db_subnet_group_arn(
                region,
                current_aws_account_id,
                subnet_group["DBSubnetGroupName"],
            )
            az = subnet.get("SubnetAvailabilityZone", {}).get("Name")
            subnets.append(
                {
                    "sn_id": sn_id,
                    "sng_arn": sng_arn,
                    "az": az,
                },
            )
    neo4j_session.run(
        attach_subnets_to_sng,
        Subnets=subnets,
        aws_update_tag=aws_update_tag,
    )


@timeit
def _attach_read_replicas(
    neo4j_session: neo4j.Session,
    read_replicas: List[Dict],
    aws_update_tag: int,
) -> None:
    """
    Attach read replicas to their source instances
    """
    attach_replica_to_source = """
    UNWIND $Replicas as rds_replica
        MATCH (replica:RDSInstance{id: rds_replica.DBInstanceArn}),
        (source:RDSInstance{db_instance_identifier: rds_replica.ReadReplicaSourceDBInstanceIdentifier})
        MERGE (replica)-[r:IS_READ_REPLICA_OF]->(source)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """
    neo4j_session.run(
        attach_replica_to_source,
        Replicas=read_replicas,
        aws_update_tag=aws_update_tag,
    )


@timeit
def _attach_clusters(
    neo4j_session: neo4j.Session,
    cluster_members: List[Dict],
    aws_update_tag: int,
) -> None:
    """
    Attach cluster members to their source clusters
    """
    attach_member_to_source = """
    UNWIND $Members as rds_cluster_member
    MATCH (member:RDSInstance{id: rds_cluster_member.DBInstanceArn}),
    (source:RDSCluster{db_cluster_identifier: rds_cluster_member.DBClusterIdentifier})
    MERGE (member)-[r:IS_CLUSTER_MEMBER_OF]->(source)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """
    neo4j_session.run(
        attach_member_to_source,
        Members=cluster_members,
        aws_update_tag=aws_update_tag,
    )


def _validate_rds_endpoint(rds: Dict) -> Dict:
    """
    Get Endpoint from RDS data structure.  Log to debug if an Endpoint field does not exist.
    """
    ep = rds.get("Endpoint", {})
    if not ep:
        logger.debug(
            "RDS instance does not have an Endpoint field.  Here is the object: %r",
            rds,
        )
    return ep


def _get_db_subnet_group_arn(
    region: str,
    current_aws_account_id: str,
    db_subnet_group_name: str,
) -> str:
    """
    Return an ARN for the DB subnet group name by concatenating the account name and region.
    This is done to avoid another AWS API call since the describe_db_instances boto call does not return the DB subnet
    group ARN.
    Form is arn:aws:rds:{region}:{account-id}:subgrp:{subnet-group-name}
    as per https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html
    """
    return (
        f"arn:aws:rds:{region}:{current_aws_account_id}:subgrp:{db_subnet_group_name}"
    )


@timeit
def transform_rds_snapshots(data: List[Dict]) -> List[Dict]:
    snapshots = []

    for snapshot in data:
        snapshots.append(snapshot)

        snapshot["SnapshotCreateTime"] = dict_value_to_str(
            snapshot,
            "EarliestRestorableTime",
        )
        snapshot["InstanceCreateTime"] = dict_value_to_str(
            snapshot,
            "InstanceCreateTime",
        )
        snapshot["ProcessorFeatures"] = dict_value_to_str(snapshot, "ProcessorFeatures")
        snapshot["OriginalSnapshotCreateTime"] = dict_value_to_str(
            snapshot,
            "OriginalSnapshotCreateTime",
        )
        snapshot["SnapshotDatabaseTime"] = dict_value_to_str(
            snapshot,
            "SnapshotDatabaseTime",
        )

    return snapshots


@timeit
def transform_rds_instances(data: List[Dict]) -> List[Dict]:
    """
    Transform RDS instance data for Neo4j ingestion
    """
    instances = []

    for instance in data:
        # Copy the instance data
        transformed_instance = instance.copy()

        # Extract security group IDs for the relationship
        security_group_ids = []
        if instance.get("VpcSecurityGroups"):
            for group in instance["VpcSecurityGroups"]:
                security_group_ids.append(group["VpcSecurityGroupId"])

        transformed_instance["security_group_ids"] = security_group_ids

        # Handle endpoint data
        ep = _validate_rds_endpoint(instance)
        transformed_instance["EndpointAddress"] = ep.get("Address")
        transformed_instance["EndpointHostedZoneId"] = ep.get("HostedZoneId")
        transformed_instance["EndpointPort"] = ep.get("Port")

        # Convert datetime fields
        transformed_instance["InstanceCreateTime"] = dict_value_to_str(
            instance, "InstanceCreateTime"
        )
        transformed_instance["LatestRestorableTime"] = dict_value_to_str(
            instance, "LatestRestorableTime"
        )

        instances.append(transformed_instance)

    return instances


@timeit
def cleanup_rds_instances_and_db_subnet_groups(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove RDS graph nodes and DBSubnetGroups that were created from other ingestion runs
    """
    run_cleanup_job(
        "aws_import_rds_instances_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def cleanup_rds_clusters(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove RDS cluster graph nodes
    """
    run_cleanup_job(
        "aws_import_rds_clusters_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def cleanup_rds_snapshots(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove RDS snapshots graph nodes
    """
    run_cleanup_job(
        "aws_import_rds_snapshots_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_rds_clusters(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Grab RDS instance data from AWS, ingest to neo4j, and run the cleanup job.
    """
    for region in regions:
        logger.info(
            "Syncing RDS for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        data = get_rds_cluster_data(boto3_session, region)
        load_rds_clusters(
            neo4j_session, data, region, current_aws_account_id, update_tag
        )
    cleanup_rds_clusters(neo4j_session, common_job_parameters)


@timeit
def sync_rds_instances(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Grab RDS instance data from AWS, ingest to neo4j, and run the cleanup job.
    """
    for region in regions:
        logger.info(
            "Syncing RDS for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        data = get_rds_instance_data(boto3_session, region)
        transformed_data = transform_rds_instances(data)
        load_rds_instances(
            neo4j_session, transformed_data, region, current_aws_account_id, update_tag
        )
    cleanup_rds_instances_and_db_subnet_groups(neo4j_session, common_job_parameters)


@timeit
def sync_rds_snapshots(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Grab RDS snapshot data from AWS, ingest to neo4j, and run the cleanup job.
    """
    for region in regions:
        logger.info(
            "Syncing RDS for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        data = get_rds_snapshot_data(boto3_session, region)
        transformed_data = transform_rds_snapshots(data)
        load_rds_snapshots(
            neo4j_session, transformed_data, region, current_aws_account_id, update_tag
        )
    cleanup_rds_snapshots(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    sync_rds_clusters(
        neo4j_session,
        boto3_session,
        regions,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )
    sync_rds_instances(
        neo4j_session,
        boto3_session,
        regions,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )
    sync_rds_snapshots(
        neo4j_session,
        boto3_session,
        regions,
        current_aws_account_id,
        update_tag,
        common_job_parameters,
    )
    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="RDSCluster",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
