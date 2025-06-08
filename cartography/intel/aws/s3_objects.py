import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.s3.s3_object import S3ObjectSchema
from cartography.stats import get_stats_client
from cartography.util import dict_date_to_epoch
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
def get_s3_object_data(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    aws_account_id: str,
    sync_limit: Optional[int],
) -> List[Dict[str, Any]]:
    """
    Get S3 object data for all buckets, respecting the sync limit.
    Returns empty list if sync is disabled (limit <= 0).
    """
    if sync_limit is not None and sync_limit <= 0:
        logger.info("S3 object sync disabled")
        return []

    buckets = get_s3_buckets_from_graph(neo4j_session, aws_account_id)
    all_objects: List[Dict[str, Any]] = []

    for bucket in buckets:
        remaining = None if sync_limit is None else sync_limit - len(all_objects)
        if remaining is not None and remaining <= 0:
            break

        objects = get_s3_objects_for_bucket(
            boto3_session,
            bucket["name"],
            bucket["region"],
            remaining,
        )

        if objects:
            transformed = transform_s3_objects(
                objects, bucket["name"], bucket["arn"], bucket["region"], aws_account_id
            )
            all_objects.extend(transformed)

    return all_objects


def get_s3_objects_for_bucket(
    boto3_session: boto3.session.Session,
    bucket_name: str,
    region: str,
    max_objects: Optional[int],
    fetch_owner: bool = False,
) -> List[Dict[str, Any]]:
    """
    Get S3 objects for a bucket.
    """
    if max_objects is not None and max_objects <= 0:
        return []

    client = boto3_session.client("s3", region_name=region)
    objects: List[Dict[str, Any]] = []

    paginator = client.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(
        Bucket=bucket_name,
        FetchOwner=fetch_owner,
        PaginationConfig={"MaxKeys": max_objects} if max_objects else {},
    )

    for page in page_iterator:
        if "Contents" in page:
            objects.extend(page["Contents"])
            if max_objects and len(objects) >= max_objects:
                objects = objects[:max_objects]
                break

    logger.info(f"Found {len(objects)} objects in bucket {bucket_name}")
    return objects


def transform_s3_objects(
    objects: List[Dict[str, Any]],
    bucket_name: str,
    bucket_arn: str,
    region: str,
    aws_account_id: str,
) -> List[Dict[str, Any]]:
    """
    Transform S3 objects to match our data model.
    """
    transformed_objects: List[Dict[str, Any]] = []

    for obj in objects:
        if obj.get("Size", 0) == 0 and obj.get("Key", "").endswith("/"):
            continue

        transformed: Dict[str, Any] = {
            "Key": obj["Key"],
            "ARN": f"{bucket_arn}/{obj['Key']}",
            "BucketName": bucket_name,
            "BucketARN": bucket_arn,
            "Size": obj.get("Size", 0),
            "StorageClass": obj.get("StorageClass", "STANDARD"),
            "LastModified": dict_date_to_epoch(obj, "LastModified"),
            "ETag": obj.get("ETag", "").strip('"'),
            "Region": region,
        }

        if "Owner" in obj:
            transformed["OwnerId"] = obj["Owner"].get("ID")
            transformed["OwnerDisplayName"] = obj["Owner"].get("DisplayName")

        if "ChecksumAlgorithm" in obj:
            transformed["ChecksumAlgorithm"] = obj["ChecksumAlgorithm"]

        if "RestoreStatus" in obj:
            transformed["IsRestoreInProgress"] = obj["RestoreStatus"].get(
                "IsRestoreInProgress"
            )
            restore_expiry = obj["RestoreStatus"].get("RestoreExpiryDate")
            if restore_expiry:
                transformed["RestoreExpiryDate"] = dict_date_to_epoch(
                    {"RestoreExpiryDate": restore_expiry}, "RestoreExpiryDate"
                )

        if "VersionId" in obj:
            transformed["VersionId"] = obj["VersionId"]
            transformed["IsLatest"] = obj.get("IsLatest", True)
            transformed["IsDeleteMarker"] = obj.get("IsDeleteMarker", False)

        transformed_objects.append(transformed)

    return transformed_objects


@timeit
def load_s3_objects(
    neo4j_session: neo4j.Session,
    objects_data: List[Dict[str, Any]],
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load S3 objects into Neo4j by region.
    """

    objects_by_region: Dict[str, List[Dict[str, Any]]] = {}
    for obj in objects_data:
        region = obj.get("Region")
        if region is None:
            logger.warning(f"S3 object missing region: {obj.get('Key', 'unknown')}")
            continue
        if region not in objects_by_region:
            objects_by_region[region] = []
        objects_by_region[region].append(obj)

    for region, region_objects in objects_by_region.items():
        logger.info(f"Loading {len(region_objects)} S3 objects for region {region}")
        load(
            neo4j_session,
            S3ObjectSchema(),
            region_objects,
            lastupdated=update_tag,
            Region=region,
            AWS_ID=aws_account_id,
        )

    # Create owner relationships if owner information is present
    owner_query = """
    MATCH (o:S3Object{lastupdated: $update_tag})
    WHERE o.owner_id IS NOT NULL
    WITH o
    MERGE (owner:AWSPrincipal{id: o.owner_id})
    ON CREATE SET owner.firstseen = timestamp()
    SET owner.lastupdated = $update_tag,
        owner.display_name = o.owner_display_name
    MERGE (owner)-[r:OWNS]->(o)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    neo4j_session.run(owner_query, update_tag=update_tag)


@timeit
def cleanup_s3_objects(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Clean up S3 objects using node schema.
    """
    logger.debug("Running S3 Objects cleanup job.")
    cleanup_job = GraphJob.from_node_schema(S3ObjectSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)


def get_s3_buckets_from_graph(
    neo4j_session: neo4j.Session,
    aws_account_id: str,
) -> List[Dict[str, Any]]:
    """
    Get S3 buckets from Neo4j to sync their objects.
    """
    query = """
    MATCH (b:S3Bucket)<-[:RESOURCE]-(a:AWSAccount{id: $account_id})
    RETURN b.name as name, b.id as arn, b.region as region
    """
    result = neo4j_session.run(query, account_id=aws_account_id)
    return [dict(record) for record in result]


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync S3 objects for account - clean pattern matching reference.
    """
    logger.info("Syncing S3 objects for account %s", current_aws_account_id)

    sync_limit = common_job_parameters.get("aws_s3_object_sync_limit")

    object_data = get_s3_object_data(
        neo4j_session,
        boto3_session,
        current_aws_account_id,
        sync_limit,
    )

    load_s3_objects(neo4j_session, object_data, current_aws_account_id, update_tag)

    stat_handler.incr("s3_objects_synced", len(object_data))

    cleanup_s3_objects(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="S3Object",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
