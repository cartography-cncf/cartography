import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.s3.s3_object import S3ObjectSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import dict_date_to_epoch
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

# Configuration constants
DEFAULT_MAX_OBJECTS_PER_BUCKET = 10000


@timeit
@aws_handle_regions
def get_s3_objects_for_bucket(
    boto3_session: boto3.session.Session,
    bucket_name: str,
    region: str,
    max_objects: int = DEFAULT_MAX_OBJECTS_PER_BUCKET,
    fetch_owner: bool = False,
) -> List[Dict]:
    """
    Get S3 objects for a specific bucket with pagination limit.

    Args:
        boto3_session: AWS session
        bucket_name: S3 bucket name
        region: AWS region
        max_objects: Maximum objects to return per bucket
        fetch_owner: Whether to fetch owner information
    """
    client = boto3_session.client("s3", region_name=region)
    objects = []

    paginator = client.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(
        Bucket=bucket_name,
        FetchOwner=fetch_owner,
        PaginationConfig={"MaxItems": max_objects},
    )

    for page in page_iterator:
        if "Contents" in page:
            objects.extend(page["Contents"])

    logger.info(f"Found {len(objects)} objects in bucket {bucket_name}")
    return objects


def transform_s3_objects(
    objects: List[Dict],
    bucket_name: str,
    bucket_arn: str,
    region: str,
    aws_account_id: str,
) -> List[Dict]:
    """
    Transform S3 objects to match our data model.
    Based on actual ListObjectsV2 response fields.
    """
    transformed_objects = []

    for obj in objects:
        # Skip folder markers (0-byte objects ending with /)
        if obj.get("Size", 0) == 0 and obj.get("Key", "").endswith("/"):
            continue

        transformed = {
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

        # Add owner fields if present (only when FetchOwner=true)
        if "Owner" in obj:
            transformed["OwnerId"] = obj["Owner"].get("ID")
            transformed["OwnerDisplayName"] = obj["Owner"].get("DisplayName")

        # Add checksum algorithm if present
        if "ChecksumAlgorithm" in obj:
            transformed["ChecksumAlgorithm"] = obj["ChecksumAlgorithm"]

        # Add restore status for archived objects (Glacier)
        if "RestoreStatus" in obj:
            transformed["IsRestoreInProgress"] = obj["RestoreStatus"].get(
                "IsRestoreInProgress"
            )
            restore_expiry = obj["RestoreStatus"].get("RestoreExpiryDate")
            if restore_expiry:
                transformed["RestoreExpiryDate"] = dict_date_to_epoch(
                    {"RestoreExpiryDate": restore_expiry}, "RestoreExpiryDate"
                )

        # Add version information if present
        if "VersionId" in obj:
            transformed["VersionId"] = obj["VersionId"]
            transformed["IsLatest"] = obj.get("IsLatest", True)
            transformed["IsDeleteMarker"] = obj.get("IsDeleteMarker", False)

        transformed_objects.append(transformed)

    return transformed_objects


@timeit
def load_s3_objects(
    neo4j_session: neo4j.Session,
    objects_data: List[Dict],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load S3 objects into Neo4j using the data model.
    """
    logger.info(
        f"Loading {len(objects_data)} S3 objects for region {region} into graph."
    )

    load(
        neo4j_session,
        S3ObjectSchema(),
        objects_data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
    )


@timeit
def cleanup_s3_objects(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """
    Clean up S3 objects using node schema.
    """
    logger.debug("Running S3 Objects cleanup job.")
    cleanup_job = GraphJob.from_node_schema(S3ObjectSchema(), common_job_parameters)
    cleanup_job.run(neo4j_session)


@timeit
def get_s3_buckets_from_graph(
    neo4j_session: neo4j.Session,
    aws_account_id: str,
) -> List[Dict]:
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
    common_job_parameters: Dict,
    max_objects_per_bucket: int = DEFAULT_MAX_OBJECTS_PER_BUCKET,
    fetch_owner: bool = False,
) -> None:
    """
    Sync S3 objects with configurable limits.
    """
    # Get buckets from graph
    buckets = get_s3_buckets_from_graph(neo4j_session, current_aws_account_id)
    logger.info(f"Found {len(buckets)} S3 buckets to process")

    total_objects_synced = 0

    for bucket in buckets:
        bucket_name = bucket["name"]
        bucket_arn = bucket["arn"]
        bucket_region = bucket["region"]

        logger.info(
            f"Syncing objects from bucket {bucket_name} in region {bucket_region}"
        )

        # Get objects - simple linear flow
        objects = get_s3_objects_for_bucket(
            boto3_session,
            bucket_name,
            bucket_region,
            max_objects_per_bucket,
            fetch_owner,
        )

        logger.info(f"Retrieved {len(objects)} objects from bucket {bucket_name}")

        # Transform
        transformed_objects = transform_s3_objects(
            objects,
            bucket_name,
            bucket_arn,
            bucket_region,
            current_aws_account_id,
        )

        # Load
        load_s3_objects(
            neo4j_session,
            transformed_objects,
            bucket_region,
            current_aws_account_id,
            update_tag,
        )

        total_objects_synced += len(transformed_objects)

    logger.info(f"Total S3 objects synced: {total_objects_synced}")

    # Cleanup
    cleanup_s3_objects(neo4j_session, common_job_parameters)

    # Update sync metadata
    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="S3Object",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
