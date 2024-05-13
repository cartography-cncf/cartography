import logging
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_snapshots_in_use(neo4j_session: neo4j.Session, region: str, current_aws_account_id: str) -> List[str]:
    query = """
    MATCH (:AWSAccount{id: $AWS_ACCOUNT_ID})-[:RESOURCE]->(v:EBSVolume)
    WHERE v.region = $Region
    RETURN v.snapshotid as snapshot
    """
    results = neo4j_session.run(query, AWS_ACCOUNT_ID=current_aws_account_id, Region=region)
    return [r['snapshot'] for r in results if r['snapshot']]


@timeit
@aws_handle_regions
def get_snapshots(boto3_session: boto3.session.Session, region: str, in_use_snapshot_ids: List[str]) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region)
    paginator = client.get_paginator('describe_snapshots')
    snapshots: List[Dict] = []
    for page in paginator.paginate(OwnerIds=['self']):
        snapshots.extend(page['Snapshots'])

    # fetch in-use snapshots not in self_owned snapshots
    self_owned_snapshot_ids = {s['SnapshotId'] for s in snapshots}
    other_snapshot_ids = set(in_use_snapshot_ids) - self_owned_snapshot_ids
    if other_snapshot_ids:
        try:
            for page in paginator.paginate(SnapshotIds=list(other_snapshot_ids)):
                snapshots.extend(page['Snapshots'])
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidSnapshot.NotFound':
                logger.warning(
                    f"Failed to retrieve page of in-use, \
                    not owned snapshots. Continuing anyway. Error - {e}",
                )
            else:
                raise

    return snapshots


@timeit
def load_snapshots(
        neo4j_session: neo4j.Session, data: List[Dict], region: str, current_aws_account_id: str, update_tag: int,
) -> None:
    ingest_snapshots = """
    UNWIND $snapshots_list as snapshot
        MERGE (s:EBSSnapshot{id: snapshot.SnapshotId})
        ON CREATE SET s.firstseen = timestamp()
        SET s.lastupdated = $update_tag, s.description = snapshot.Description, s.encrypted = snapshot.Encrypted,
        s.progress = snapshot.Progress, s.starttime = snapshot.StartTime, s.state = snapshot.State,
        s.statemessage = snapshot.StateMessage, s.volumeid = snapshot.VolumeId, s.volumesize = snapshot.VolumeSize,
        s.outpostarn = snapshot.OutpostArn, s.dataencryptionkeyid = snapshot.DataEncryptionKeyId,
        s.kmskeyid = snapshot.KmsKeyId, s.region=$Region
        WITH s
        MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (aa)-[r:RESOURCE]->(s)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """

    for snapshot in data:
        snapshot['StartTime'] = str(snapshot['StartTime'])

    neo4j_session.run(
        ingest_snapshots,
        snapshots_list=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        Region=region,
        update_tag=update_tag,
    )


@timeit
def get_snapshot_volumes(snapshots: List[Dict]) -> List[Dict]:
    snapshot_volumes: List[Dict] = []
    for snapshot in snapshots:
        if snapshot.get('VolumeId'):
            snapshot_volumes.append(snapshot)

    return snapshot_volumes


@timeit
def load_snapshot_volume_relations(
        neo4j_session: neo4j.Session, data: List[Dict], current_aws_account_id: str, update_tag: int,
) -> None:
    ingest_volumes = """
    UNWIND $snapshot_volumes_list as volume
        MERGE (v:EBSVolume{id: volume.VolumeId})
        ON CREATE SET v.firstseen = timestamp()
        SET v.lastupdated = $update_tag, v.snapshotid = volume.SnapshotId
        WITH v, volume
        MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (aa)-[r:RESOURCE]->(v)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
        WITH v, volume
        MATCH (s:EBSSnapshot{id: volume.SnapshotId})
        MERGE (s)-[r:CREATED_FROM]->(v)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """

    neo4j_session.run(
        ingest_volumes,
        snapshot_volumes_list=data,
        AWS_ACCOUNT_ID=current_aws_account_id,
        update_tag=update_tag,
    )


@timeit
def cleanup_snapshots(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        'aws_import_snapshots_cleanup.json',
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync_ebs_snapshots(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
        current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.debug("Syncing snapshots for region '%s' in account '%s'.", region, current_aws_account_id)
        snapshots_in_use = get_snapshots_in_use(neo4j_session, region, current_aws_account_id)
        data = get_snapshots(boto3_session, region, snapshots_in_use)
        load_snapshots(neo4j_session, data, region, current_aws_account_id, update_tag)
        snapshot_volumes = get_snapshot_volumes(data)
        load_snapshot_volume_relations(neo4j_session, snapshot_volumes, current_aws_account_id, update_tag)
    cleanup_snapshots(neo4j_session, common_job_parameters)
