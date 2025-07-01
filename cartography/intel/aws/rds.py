import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

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
    data: Dict,
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Ingest the RDS clusters to neo4j and link them to necessary nodes.
    """
    ingest_rds_cluster = """
    UNWIND $Clusters as rds_cluster
        MERGE (cluster:RDSCluster{id: rds_cluster.DBClusterArn})
        ON CREATE SET cluster.firstseen = timestamp(),
            cluster.arn = rds_cluster.DBClusterArn
        SET cluster.allocated_storage = rds_cluster.AllocatedStorage,
            cluster.availability_zones = rds_cluster.AvailabilityZones,
            cluster.backup_retention_period = rds_cluster.BackupRetentionPeriod,
            cluster.character_set_name = rds_cluster.CharacterSetName,
            cluster.database_name = rds_cluster.DatabaseName,
            cluster.db_cluster_identifier = rds_cluster.DBClusterIdentifier,
            cluster.db_parameter_group = rds_cluster.DBClusterParameterGroup,
            cluster.status = rds_cluster.Status,
            cluster.earliest_restorable_time = rds_cluster.EarliestRestorableTime,
            cluster.endpoint = rds_cluster.Endpoint,
            cluster.reader_endpoint = rds_cluster.ReaderEndpoint,
            cluster.multi_az = rds_cluster.MultiAZ,
            cluster.engine = rds_cluster.Engine,
            cluster.engine_version = rds_cluster.EngineVersion,
            cluster.latest_restorable_time = rds_cluster.LatestRestorableTime,
            cluster.port = rds_cluster.Port,
            cluster.master_username = rds_cluster.MasterUsername,
            cluster.preferred_backup_window = rds_cluster.PreferredBackupWindow,
            cluster.preferred_maintenance_window = rds_cluster.PreferredMaintenanceWindow,
            cluster.hosted_zone_id = rds_cluster.HostedZoneId,
            cluster.storage_encrypted = rds_cluster.StorageEncrypted,
            cluster.kms_key_id = rds_cluster.KmsKeyId,
            cluster.db_cluster_resource_id = rds_cluster.DbClusterResourceId,
            cluster.clone_group_id = rds_cluster.CloneGroupId,
            cluster.cluster_create_time = rds_cluster.ClusterCreateTime,
            cluster.earliest_backtrack_time = rds_cluster.EarliestBacktrackTime,
            cluster.backtrack_window = rds_cluster.BacktrackWindow,
            cluster.backtrack_consumed_change_records = rds_cluster.BacktrackConsumedChangeRecords,
            cluster.capacity = rds_cluster.Capacity,
            cluster.engine_mode = rds_cluster.EngineMode,
            cluster.scaling_configuration_info_min_capacity = rds_cluster.ScalingConfigurationInfoMinCapacity,
            cluster.scaling_configuration_info_max_capacity = rds_cluster.ScalingConfigurationInfoMaxCapacity,
            cluster.scaling_configuration_info_auto_pause = rds_cluster.ScalingConfigurationInfoAutoPause,
            cluster.deletion_protection = rds_cluster.DeletionProtection,
            cluster.region = $Region,
            cluster.lastupdated = $aws_update_tag
        WITH cluster
        MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (aa)-[r:RESOURCE]->(cluster)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """
    for cluster in data:
        # TODO: track read replicas
        # TODO: track associated roles
        # TODO: track security groups
        # TODO: track subnet groups

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

    neo4j_session.run(
        ingest_rds_cluster,
        Clusters=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
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
    data: Dict,
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Ingest the RDS instances to neo4j and link them to necessary nodes.
    """
    ingest_rds_instance = """
    UNWIND $Instances as rds_instance
        MERGE (rds:RDSInstance{id: rds_instance.DBInstanceArn})
        ON CREATE SET rds.firstseen = timestamp(),
            rds.arn = rds_instance.DBInstanceArn
        SET rds.db_instance_identifier = rds_instance.DBInstanceIdentifier,
            rds.db_instance_class = rds_instance.DBInstanceClass,
            rds.engine = rds_instance.Engine,
            rds.master_username = rds_instance.MasterUsername,
            rds.db_name = rds_instance.DBName,
            rds.instance_create_time = rds_instance.InstanceCreateTime,
            rds.availability_zone = rds_instance.AvailabilityZone,
            rds.multi_az = rds_instance.MultiAZ,
            rds.engine_version = rds_instance.EngineVersion,
            rds.publicly_accessible = rds_instance.PubliclyAccessible,
            rds.db_cluster_identifier = rds_instance.DBClusterIdentifier,
            rds.storage_encrypted = rds_instance.StorageEncrypted,
            rds.kms_key_id = rds_instance.KmsKeyId,
            rds.dbi_resource_id = rds_instance.DbiResourceId,
            rds.ca_certificate_identifier = rds_instance.CACertificateIdentifier,
            rds.enhanced_monitoring_resource_arn = rds_instance.EnhancedMonitoringResourceArn,
            rds.monitoring_role_arn = rds_instance.MonitoringRoleArn,
            rds.performance_insights_enabled = rds_instance.PerformanceInsightsEnabled,
            rds.performance_insights_kms_key_id = rds_instance.PerformanceInsightsKMSKeyId,
            rds.region = rds_instance.Region,
            rds.deletion_protection = rds_instance.DeletionProtection,
            rds.preferred_backup_window = rds_instance.PreferredBackupWindow,
            rds.latest_restorable_time = rds_instance.LatestRestorableTime,
            rds.preferred_maintenance_window = rds_instance.PreferredMaintenanceWindow,
            rds.backup_retention_period = rds_instance.BackupRetentionPeriod,
            rds.endpoint_address = rds_instance.EndpointAddress,
            rds.endpoint_hostedzoneid = rds_instance.EndpointHostedZoneId,
            rds.endpoint_port = rds_instance.EndpointPort,
            rds.iam_database_authentication_enabled = rds_instance.IAMDatabaseAuthenticationEnabled,
            rds.auto_minor_version_upgrade = rds_instance.AutoMinorVersionUpgrade,
            rds.lastupdated = $aws_update_tag
        WITH rds
        MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (aa)-[r:RESOURCE]->(rds)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """
    read_replicas = []
    clusters = []
    secgroups = []
    subnets = []

    for rds in data:
        ep = _validate_rds_endpoint(rds)

        # Keep track of instances that are read replicas so we can attach them to their source instances later
        if rds.get("ReadReplicaSourceDBInstanceIdentifier"):
            read_replicas.append(rds)

        # Keep track of instances that are cluster members so we can attach them to their source clusters later
        if rds.get("DBClusterIdentifier"):
            clusters.append(rds)

        if rds.get("VpcSecurityGroups"):
            secgroups.append(rds)

        if rds.get("DBSubnetGroup"):
            subnets.append(rds)

        rds["InstanceCreateTime"] = dict_value_to_str(rds, "InstanceCreateTime")
        rds["LatestRestorableTime"] = dict_value_to_str(rds, "LatestRestorableTime")
        rds["EndpointAddress"] = ep.get("Address")
        rds["EndpointHostedZoneId"] = ep.get("HostedZoneId")
        rds["EndpointPort"] = ep.get("Port")

    neo4j_session.run(
        ingest_rds_instance,
        Instances=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )
    _attach_ec2_security_groups(neo4j_session, secgroups, aws_update_tag)
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
    data: Dict,
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Ingest the RDS snapshots to neo4j and link them to necessary nodes.
    """
    ingest_rds_snapshot = """
    UNWIND $Snapshots as rds_snapshot
        MERGE (snapshot:RDSSnapshot{id: rds_snapshot.DBSnapshotArn})
        ON CREATE SET snapshot.firstseen = timestamp(),
            snapshot.arn = rds_snapshot.DBSnapshotArn
        SET snapshot.db_snapshot_identifier = rds_snapshot.DBSnapshotIdentifier,
            snapshot.db_instance_identifier = rds_snapshot.DBInstanceIdentifier,
            snapshot.snapshot_create_time = rds_snapshot.SnapshotCreateTime,
            snapshot.engine = rds_snapshot.Engine,
            snapshot.allocated_storage = rds_snapshot.AllocatedStorage,
            snapshot.status = rds_snapshot.Status,
            snapshot.port = rds_snapshot.Port,
            snapshot.availability_zone = rds_snapshot.AvailabilityZone,
            snapshot.vpc_id = rds_snapshot.VpcId,
            snapshot.instance_create_time = rds_snapshot.InstanceCreateTime,
            snapshot.master_username = rds_snapshot.MasterUsername,
            snapshot.engine_version = rds_snapshot.EngineVersion,
            snapshot.license_model = rds_snapshot.LicenseModel,
            snapshot.snapshot_type = rds_snapshot.SnapshotType,
            snapshot.iops = rds_snapshot.Iops,
            snapshot.option_group_name = rds_snapshot.OptionGroupName,
            snapshot.percent_progress = rds_snapshot.PercentProgress,
            snapshot.source_region = rds_snapshot.SourceRegion,
            snapshot.source_db_snapshot_identifier = rds_snapshot.SourceDBSnapshotIdentifier,
            snapshot.storage_type = rds_snapshot.StorageType,
            snapshot.tde_credential_arn = rds_snapshot.TdeCredentialArn,
            snapshot.encrypted = rds_snapshot.Encrypted,
            snapshot.kms_key_id = rds_snapshot.KmsKeyId,
            snapshot.timezone = rds_snapshot.Timezone,
            snapshot.iam_database_authentication_enabled = rds_snapshot.IAMDatabaseAuthenticationEnabled,
            snapshot.processor_features = rds_snapshot.ProcessorFeatures,
            snapshot.dbi_resource_id = rds_snapshot.DbiResourceId,
            snapshot.original_snapshot_create_time = rds_snapshot.OriginalSnapshotCreateTime,
            snapshot.snapshot_database_time = rds_snapshot.SnapshotDatabaseTime,
            snapshot.snapshot_target = rds_snapshot.SnapshotTarget,
            snapshot.storage_throughput = rds_snapshot.StorageThroughput,
            snapshot.region = $Region,
            snapshot.lastupdated = $aws_update_tag
        WITH snapshot
        MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (aa)-[r:RESOURCE]->(snapshot)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """

    snapshots = transform_rds_snapshots(data)

    neo4j_session.run(
        ingest_rds_snapshot,
        Snapshots=snapshots,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )
    _attach_snapshots(neo4j_session, snapshots, aws_update_tag)


@timeit
def _attach_snapshots(
    neo4j_session: neo4j.Session,
    snapshots: List[Dict],
    aws_update_tag: int,
) -> None:
    """
    Attach snapshots to their source instance
    """
    attach_member_to_source = """
    UNWIND $Snapshots as snapshot
        MATCH (rdsInstance:RDSInstance {db_instance_identifier: snapshot.DBInstanceIdentifier}),
        (rdsSnapshot:RDSSnapshot {arn: snapshot.DBSnapshotArn})
        MERGE (rdsInstance)-[r:IS_SNAPSHOT_SOURCE]->(rdsSnapshot)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """
    neo4j_session.run(
        attach_member_to_source,
        Snapshots=snapshots,
        aws_update_tag=aws_update_tag,
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
def _attach_ec2_security_groups(
    neo4j_session: neo4j.Session,
    instances: List[Dict],
    aws_update_tag: int,
) -> None:
    """
    Attach an RDS instance to its EC2SecurityGroups
    """
    attach_rds_to_group = """
    UNWIND $Groups as rds_sg
        MATCH (rds:RDSInstance{id: rds_sg.arn})
        MERGE (sg:EC2SecurityGroup{id: rds_sg.group_id})
        MERGE (rds)-[m:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
        ON CREATE SET m.firstseen = timestamp()
        SET m.lastupdated = $aws_update_tag
    """
    groups = []
    for instance in instances:
        for group in instance["VpcSecurityGroups"]:
            groups.append(
                {
                    "arn": instance["DBInstanceArn"],
                    "group_id": group["VpcSecurityGroupId"],
                },
            )
    neo4j_session.run(
        attach_rds_to_group,
        Groups=groups,
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
def transform_rds_snapshots(data: Dict) -> List[Dict]:
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
        load_rds_clusters(neo4j_session, data, region, current_aws_account_id, update_tag)  # type: ignore
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
        load_rds_instances(neo4j_session, data, region, current_aws_account_id, update_tag)  # type: ignore
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
        load_rds_snapshots(neo4j_session, data, region, current_aws_account_id, update_tag)  # type: ignore
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
