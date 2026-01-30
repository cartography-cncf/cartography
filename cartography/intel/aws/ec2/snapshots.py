import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError

from cartography.client.core.tx import load
from cartography.client.core.tx import read_list_of_values_tx
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.snapshots import EBSSnapshotSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_snapshots_in_use(
    neo4j_session: neo4j.Session,
    region: str,
    current_aws_account_id: str,
) -> List[str]:
    query = """
    MATCH (:AWSAccount{id: $AWS_ACCOUNT_ID})-[:RESOURCE]->(v:EBSVolume)
    WHERE v.region = $Region
    RETURN v.snapshotid as snapshot
    """
    results = read_list_of_values_tx(
        neo4j_session,
        query,
        AWS_ACCOUNT_ID=current_aws_account_id,
        Region=region,
    )
    return [str(snapshot) for snapshot in results if snapshot]


@timeit
@aws_handle_regions
def get_snapshots(
    boto3_session: boto3.session.Session,
    region: str,
    in_use_snapshot_ids: List[str],
) -> List[Dict]:
    client = boto3_session.client("ec2", region_name=region)
    paginator = client.get_paginator("describe_snapshots")
    snapshots: List[Dict] = []
    for page in paginator.paginate(OwnerIds=["self"]):
        snapshots.extend(page["Snapshots"])

    self_owned_snapshot_ids = {s["SnapshotId"] for s in snapshots}
    other_snapshot_ids = set(in_use_snapshot_ids) - self_owned_snapshot_ids
    if other_snapshot_ids:
        try:
            for page in paginator.paginate(SnapshotIds=list(other_snapshot_ids)):
                snapshots.extend(page["Snapshots"])
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidSnapshot.NotFound":
                logger.warning(
                    f"Failed to retrieve page of in-use, not owned snapshots. Continuing anyway. Error - {e}"
                )
            else:
                raise

    return snapshots


def transform_snapshots(snapshots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    transformed: List[Dict[str, Any]] = []
    for snap in snapshots:
        transformed.append(
            {
                "SnapshotId": snap["SnapshotId"],
                "Description": snap.get("Description"),
                "Encrypted": snap.get("Encrypted"),
                "Progress": snap.get("Progress"),
                "StartTime": snap.get("StartTime"),
                "State": snap.get("State"),
                "StateMessage": snap.get("StateMessage"),
                "VolumeId": snap.get("VolumeId"),
                "VolumeSize": snap.get("VolumeSize"),
                "OutpostArn": snap.get("OutpostArn"),
                "DataEncryptionKeyId": snap.get("DataEncryptionKeyId"),
                "KmsKeyId": snap.get("KmsKeyId"),
            }
        )
    return transformed


@timeit
def load_snapshots(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EBSSnapshotSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup_snapshots(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    GraphJob.from_node_schema(EBSSnapshotSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_ebs_snapshots(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    for region in regions:
        logger.debug(
            "Syncing snapshots for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        snapshots_in_use = get_snapshots_in_use(
            neo4j_session,
            region,
            current_aws_account_id,
        )
        raw_data = get_snapshots(boto3_session, region, snapshots_in_use)
        transformed_data = transform_snapshots(raw_data)
        load_snapshots(
            neo4j_session,
            transformed_data,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup_snapshots(neo4j_session, common_job_parameters)
