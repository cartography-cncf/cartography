import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.efs.access_point import EfsAccessPointSchema
from cartography.models.aws.efs.file_system import EfsFileSystemSchema
from cartography.models.aws.efs.mount_target import EfsMountTargetSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_efs_file_systems(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "efs", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("describe_file_systems")
    fileSystems = []
    for page in paginator.paginate():
        fileSystems.extend(page.get("FileSystems", []))

    return fileSystems


def transform_efs_file_systems(
    fileSystems: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    """
    Transform SNS topic data for ingestion
    """
    transformed_file_systems = []
    for file_system in fileSystems:
        transformed_file_system = {
            "FileSystemId": file_system["FileSystemId"],
            "FileSystemArn": file_system["FileSystemArn"],
            "Region": region,
            "OwnerId": file_system.get("OwnerId"),
            "CreationToken": file_system.get("CreationToken"),
            "CreationTime": file_system.get("CreationTime"),
            "LifeCycleState": file_system.get("LifeCycleState"),
            "Name": file_system.get("Name"),
            "NumberOfMountTargets": file_system.get("NumberOfMountTargets"),
            "SizeInBytesValue": file_system.get("SizeInBytes", {}).get("Value"),
            "SizeInBytesTimestamp": file_system.get("SizeInBytes", {}).get("Timestamp"),
            "PerformanceMode": file_system.get("PerformanceMode"),
            "Encrypted": file_system.get("Encrypted"),
            "KmsKeyId": file_system.get("KmsKeyId"),
            "ThroughputMode": file_system.get("ThroughputMode"),
            "AvailabilityZoneName": file_system.get("AvailabilityZoneName"),
            "AvailabilityZoneId": file_system.get("AvailabilityZoneId"),
            "FileSystemProtection": file_system.get("FileSystemProtection", {}).get(
                "ReplicationOverwriteProtection"
            ),
        }
        transformed_file_systems.append(transformed_file_system)

    return transformed_file_systems


@timeit
@aws_handle_regions
def get_efs_mount_targets(
    fileSystems: List[Dict[str, Any]], boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "efs", region_name=region, config=get_botocore_config()
    )
    file_system_ids = []
    for file_system in fileSystems:
        file_system_ids.append(file_system["FileSystemId"])
    paginator = client.get_paginator("describe_mount_targets")
    mountTargets = []
    for fs_id in file_system_ids:
        for page in paginator.paginate(FileSystemId=fs_id):
            mountTargets.extend(page.get("MountTargets", []))

    return mountTargets


@timeit
@aws_handle_regions
def get_efs_access_points(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "efs", region_name=region, config=get_botocore_config()
    )

    paginator = client.get_paginator("describe_access_points")
    accessPoints = []
    for page in paginator.paginate():
        accessPoints.extend(page.get("AccessPoints", []))

    return accessPoints


def transform_efs_access_points(
    accessPoints: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    """
    Transform Efs Access Points data for ingestion
    """
    transformed = []
    for ap in accessPoints:
        transformed.append(
            {
                "AccessPointArn": ap["AccessPointArn"],
                "AccessPointId": ap["AccessPointId"],
                "Region": region,
                "FileSystemId": ap["FileSystemId"],
                "Name": ap.get("Name"),
                "LifeCycleState": ap.get("LifeCycleState"),
                "OwnerId": ap.get("OwnerId"),
                "Uid": ap.get("PosixUser", {}).get("Uid"),
                "Gid": ap.get("PosixUser", {}).get("Gid"),
                "RootDirectoryPath": ap.get("RootDirectory", {}).get("Path"),
            }
        )

    return transformed


@timeit
def load_efs_mount_targets(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading Efs {len(data)} mount targets for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        EfsMountTargetSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_efs_file_systems(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading Efs {len(data)} file systems for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        EfsFileSystemSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_efs_access_points(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading Efs {len(data)} access points for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        EfsAccessPointSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Running Efs cleanup job.")
    GraphJob.from_node_schema(EfsMountTargetSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(EfsFileSystemSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(EfsAccessPointSchema(), common_job_parameters).run(
        neo4j_session
    )


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
            f"Syncing Efs for region '{region}' in account '{current_aws_account_id}'.",
        )

        fileSystems = get_efs_file_systems(boto3_session, region)
        tranformed_file_systems = transform_efs_file_systems(fileSystems, region)

        load_efs_file_systems(
            neo4j_session,
            tranformed_file_systems,
            region,
            current_aws_account_id,
            update_tag,
        )

        mountTargets = get_efs_mount_targets(fileSystems, boto3_session, region)

        load_efs_mount_targets(
            neo4j_session,
            mountTargets,
            region,
            current_aws_account_id,
            update_tag,
        )

        accessPoints = get_efs_access_points(boto3_session, region)
        accessPoints_transformed = transform_efs_access_points(accessPoints, region)

        load_efs_access_points(
            neo4j_session,
            accessPoints_transformed,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
