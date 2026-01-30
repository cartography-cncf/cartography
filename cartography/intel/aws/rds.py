import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.rds.cluster import RDSClusterSchema
from cartography.models.aws.rds.event_subscription import RDSEventSubscriptionSchema
from cartography.models.aws.rds.instance import RDSInstanceSchema
from cartography.models.aws.rds.snapshot import RDSSnapshotSchema
from cartography.models.aws.rds.subnet_group import DBSubnetGroupSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import aws_paginate
from cartography.util import dict_value_to_str
from cartography.util import merge_module_sync_metadata
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
    load(
        neo4j_session,
        RDSInstanceSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


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
@aws_handle_regions
def get_rds_event_subscription_data(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict[str, Any]]:
    client = boto3_session.client("rds", region_name=region)
    paginator = client.get_paginator("describe_event_subscriptions")
    subscriptions = []
    for page in paginator.paginate():
        subscriptions.extend(page["EventSubscriptionsList"])
    return subscriptions


@timeit
def load_rds_event_subscriptions(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        RDSEventSubscriptionSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
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


def transform_rds_clusters(data: List[Dict]) -> List[Dict]:
    """
    Transform RDS cluster data for Neo4j ingestion
    """
    clusters = []

    for cluster in data:
        # Copy the cluster data
        transformed_cluster = cluster.copy()

        # Convert datetime fields
        transformed_cluster["EarliestRestorableTime"] = dict_value_to_str(
            cluster, "EarliestRestorableTime"
        )
        transformed_cluster["LatestRestorableTime"] = dict_value_to_str(
            cluster, "LatestRestorableTime"
        )
        transformed_cluster["ClusterCreateTime"] = dict_value_to_str(
            cluster, "ClusterCreateTime"
        )
        transformed_cluster["EarliestBacktrackTime"] = dict_value_to_str(
            cluster, "EarliestBacktrackTime"
        )

        # Extract scaling configuration info
        scaling_config = cluster.get("ScalingConfigurationInfo", {})
        transformed_cluster["ScalingConfigurationInfoMinCapacity"] = scaling_config.get(
            "MinCapacity"
        )
        transformed_cluster["ScalingConfigurationInfoMaxCapacity"] = scaling_config.get(
            "MaxCapacity"
        )
        transformed_cluster["ScalingConfigurationInfoAutoPause"] = scaling_config.get(
            "AutoPause"
        )

        clusters.append(transformed_cluster)

    return clusters


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


def transform_rds_instances(
    data: List[Dict], region: str, current_aws_account_id: str
) -> List[Dict]:
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

        # Handle read replica source identifier for the relationship
        if instance.get("ReadReplicaSourceDBInstanceIdentifier"):
            transformed_instance["read_replica_source_identifier"] = instance[
                "ReadReplicaSourceDBInstanceIdentifier"
            ]

        # Handle cluster identifier for the relationship
        if instance.get("DBClusterIdentifier"):
            transformed_instance["db_cluster_identifier"] = instance[
                "DBClusterIdentifier"
            ]

        # Handle subnet group data for the relationship
        if instance.get("DBSubnetGroup"):
            db_subnet_group = instance["DBSubnetGroup"]
            transformed_instance["db_subnet_group_arn"] = _get_db_subnet_group_arn(
                region, current_aws_account_id, db_subnet_group["DBSubnetGroupName"]
            )

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


def transform_rds_event_subscriptions(data: List[Dict]) -> List[Dict]:
    subscriptions = []
    for subscription in data:
        transformed = {
            "CustSubscriptionId": subscription.get("CustSubscriptionId"),
            "EventSubscriptionArn": subscription.get("EventSubscriptionArn"),
            "CustomerAwsId": subscription.get("CustomerAwsId"),
            "SnsTopicArn": subscription.get("SnsTopicArn"),
            "SourceType": subscription.get("SourceType"),
            "Status": subscription.get("Status"),
            "Enabled": subscription.get("Enabled"),
            "SubscriptionCreationTime": dict_value_to_str(
                subscription, "SubscriptionCreationTime"
            ),
            "event_categories": subscription.get("EventCategoriesList") or None,
            "source_ids": subscription.get("SourceIdsList") or None,
            "lastupdated": None,  # This will be set by the loader
        }
        subscriptions.append(transformed)
    return subscriptions


def transform_rds_subnet_groups(
    data: List[Dict], region: str, current_aws_account_id: str
) -> List[Dict]:
    """
    Transform RDS subnet group data for Neo4j ingestion
    """
    subnet_groups_dict = {}

    for instance in data:
        if instance.get("DBSubnetGroup"):
            db_subnet_group = instance["DBSubnetGroup"]
            db_subnet_group_arn = _get_db_subnet_group_arn(
                region, current_aws_account_id, db_subnet_group["DBSubnetGroupName"]
            )

            # If this subnet group doesn't exist yet, create it
            if db_subnet_group_arn not in subnet_groups_dict:
                subnet_groups_dict[db_subnet_group_arn] = {
                    "id": db_subnet_group_arn,
                    "name": db_subnet_group["DBSubnetGroupName"],
                    "vpc_id": db_subnet_group["VpcId"],
                    "description": db_subnet_group["DBSubnetGroupDescription"],
                    "status": db_subnet_group["SubnetGroupStatus"],
                    "db_instance_identifier": [],
                    "subnet_ids": [],
                }

            # Add this RDS instance to the subnet group's list
            if instance.get("DBInstanceIdentifier"):
                subnet_groups_dict[db_subnet_group_arn][
                    "db_instance_identifier"
                ].append(instance["DBInstanceIdentifier"])

            # Add subnet IDs from the DB subnet group
            for subnet in db_subnet_group.get("Subnets", []):
                subnet_id = subnet.get("SubnetIdentifier")
                if (
                    subnet_id
                    and subnet_id
                    not in subnet_groups_dict[db_subnet_group_arn]["subnet_ids"]
                ):
                    subnet_groups_dict[db_subnet_group_arn]["subnet_ids"].append(
                        subnet_id
                    )

    return list(subnet_groups_dict.values())


@timeit
def load_rds_subnet_groups(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Ingest the RDS subnet groups to Neo4j and link them to necessary nodes.
    """
    load(
        neo4j_session,
        DBSubnetGroupSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup_rds_instances_and_db_subnet_groups(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove RDS instances and DB subnet groups that weren't updated in this sync run
    """
    logger.debug("Running RDS instances and DB subnet groups cleanup job")

    # Clean up RDS instances
    GraphJob.from_node_schema(RDSInstanceSchema(), common_job_parameters).run(
        neo4j_session
    )

    # Clean up DB subnet groups
    GraphJob.from_node_schema(DBSubnetGroupSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_rds_clusters(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove RDS clusters that weren't updated in this sync run
    """
    logger.debug("Running RDS clusters cleanup job")

    GraphJob.from_node_schema(RDSClusterSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_rds_snapshots(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove RDS snapshots that weren't updated in this sync run
    """
    logger.debug("Running RDS snapshots cleanup job")

    GraphJob.from_node_schema(RDSSnapshotSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def cleanup_rds_event_subscriptions(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Remove RDS event subscriptions that weren't updated in this sync run
    """
    logger.debug("Running RDS event subscriptions cleanup job")
    GraphJob.from_node_schema(RDSEventSubscriptionSchema(), common_job_parameters).run(
        neo4j_session
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
    Grab RDS cluster data from AWS, ingest to neo4j, and run the cleanup job.
    """
    for region in regions:
        logger.info(
            "Syncing RDS clusters for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        data = get_rds_cluster_data(boto3_session, region)
        transformed_data = transform_rds_clusters(data)
        load_rds_clusters(
            neo4j_session, transformed_data, region, current_aws_account_id, update_tag
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
            "Syncing RDS instances for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        data = get_rds_instance_data(boto3_session, region)
        transformed_data = transform_rds_instances(data, region, current_aws_account_id)
        load_rds_instances(
            neo4j_session, transformed_data, region, current_aws_account_id, update_tag
        )

        # Load subnet groups from RDS instances
        subnet_group_data = transform_rds_subnet_groups(
            data, region, current_aws_account_id
        )
        load_rds_subnet_groups(
            neo4j_session, subnet_group_data, region, current_aws_account_id, update_tag
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
            "Syncing RDS snapshots for region '%s' in account '%s'.",
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
def sync_rds_event_subscriptions(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Grab RDS event subscription data from AWS, ingest to neo4j, and run the cleanup job.
    """
    for region in regions:
        logger.info(
            "Syncing RDS event subscriptions for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        data = get_rds_event_subscription_data(boto3_session, region)
        transformed = transform_rds_event_subscriptions(data)
        load_rds_event_subscriptions(
            neo4j_session, transformed, region, current_aws_account_id, update_tag
        )
    cleanup_rds_event_subscriptions(neo4j_session, common_job_parameters)


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

    sync_rds_event_subscriptions(
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
