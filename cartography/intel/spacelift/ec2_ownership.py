import json
import logging
import re
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.spacelift.cloudtrailevent import CloudTrailEventSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Regex pattern to match EC2 instance IDs
INSTANCE_ID_PATTERN = re.compile(r"\b(i-[0-9a-f]{8,17})\b")


@aws_handle_regions
@timeit
def get_ec2_ownership(
    aws_session: boto3.Session, bucket_name: str, object_prefix: str
) -> list[dict[str, Any]]:
    """
    Fetch EC2 ownership data from all JSON files under an S3 prefix containing Athena query results.

    Args:
        aws_session: AWS session for making S3 requests
        bucket_name: S3 bucket name
        object_prefix: S3 prefix to search for JSON files. Trailing slash is optional and will be normalized.

    Returns:
        Aggregated list of CloudTrail records from all JSON files under the prefix
    """
    # Normalize prefix - ensure it ends with '/' to treat it as a directory
    # This prevents matching prefixes like "data" matching "data-backup" objects
    normalized_prefix = object_prefix.rstrip("/") + "/" if object_prefix else ""

    logger.info(
        f"Fetching EC2 ownership data from s3://{bucket_name}/{normalized_prefix}"
    )

    # Create S3 client from the boto3 session
    s3_client = aws_session.client("s3")

    paginator = s3_client.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=normalized_prefix)

    all_records = []
    total_files_processed = 0

    for page in page_iterator:
        if "Contents" not in page:
            logger.warning(
                f"No objects found under prefix s3://{bucket_name}/{normalized_prefix}"
            )
            continue

        # Filter for JSON files and exclude the prefix itself if it appears as an object
        json_files = [
            obj
            for obj in page["Contents"]
            if obj["Key"].endswith(".json") and obj["Key"] != normalized_prefix
        ]

        if not json_files:
            continue

        logger.info(f"Found {len(json_files)} JSON files to process in this page")

        for s3_object in json_files:
            object_key = s3_object["Key"]
            logger.info(f"Processing {object_key}")

            try:
                response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
                object_body = response["Body"].read()
                json_content = json.loads(object_body.decode("utf-8"))

                # Handle both single objects and arrays
                if isinstance(json_content, list):
                    all_records.extend(json_content)
                    records_added = len(json_content)
                else:
                    all_records.append(json_content)
                    records_added = 1

                total_files_processed += 1
                logger.info(
                    f"Successfully processed {object_key}, added {records_added} records"
                )

            except Exception as e:
                logger.error(f"Failed to process {object_key}: {e}")
                continue

    logger.info(
        f"Successfully processed {total_files_processed} files and fetched {len(all_records)} total CloudTrail records from S3"
    )

    return all_records


def extract_spacelift_run_id(useridentity_str: str) -> str | None:
    """
    Extract Spacelift run ID from the useridentity field.
    """
    # Only process if 'spacelift' is in the useridentity
    if "spacelift" not in useridentity_str.lower():
        return None

    # Extract the ARN using regex
    # Format: arn=arn:aws:sts::ACCOUNT:assumed-role/ROLE_NAME/SESSION_NAME
    arn_match = re.search(
        r"arn=arn:aws:sts::[^:]+:assumed-role/[^/]+/([^,}]+)", useridentity_str
    )

    if not arn_match:
        return None

    session_name = arn_match.group(1).strip()

    # Run ID is the first part before the @ symbol
    run_id = session_name.split("@")[0]

    return run_id if run_id else None


def extract_instance_ids(record: dict[str, Any]) -> list[str]:
    """
    Extract EC2 instance IDs from a CloudTrail record.
    """
    instance_ids = set()

    # Check resources field
    resources = record.get("resources")
    if resources:
        resources_str = str(resources)
        instance_ids.update(INSTANCE_ID_PATTERN.findall(resources_str))

    # Check requestparameters field
    request_params = record.get("requestparameters")
    if request_params:
        instance_ids.update(INSTANCE_ID_PATTERN.findall(str(request_params)))

    # Check responseelements field
    response_elements = record.get("responseelements")
    if response_elements:
        instance_ids.update(INSTANCE_ID_PATTERN.findall(str(response_elements)))

    return list(instance_ids)


@timeit
def transform_ec2_ownership(
    cloudtrail_data: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Transform CloudTrail data to create CloudTrailEvent nodes.

    This function filters CloudTrail records to find those that have BOTH:
    1. A Spacelift run ID (from the useridentity field)
    2. One or more EC2 instance IDs (from resources, requestparameters, or responseelements)

    Each CloudTrail record becomes one CloudTrailEvent node that can connect to multiple instances.
    """
    logger.info(
        f"Transforming {len(cloudtrail_data)} CloudTrail records to create CloudTrailEvent nodes"
    )

    events = []

    for record in cloudtrail_data:
        # Extract run ID from useridentity
        useridentity = record.get("useridentity", "")
        run_id = extract_spacelift_run_id(useridentity)

        if not run_id:
            # Skip records without Spacelift run IDs
            continue

        # Extract instance IDs
        instance_ids = extract_instance_ids(record)

        if not instance_ids:
            # Skip records without instance IDs
            continue

        # Create one event node per CloudTrail event (using CloudTrail's native eventid)
        event_id = record.get("eventid")
        if not event_id:
            # Fallback: shouldn't happen with real CloudTrail data
            logger.warning(
                f"CloudTrail event missing eventid field for run {run_id}, skipping"
            )
            continue

        event = {
            "id": event_id,
            "run_id": run_id,
            "instance_ids": instance_ids,  # List of instances affected by this event
            "event_time": record.get("eventtime"),
            "event_name": record.get("eventname"),
            "aws_account": record.get("account"),
            "aws_region": record.get("awsregion"),
        }
        events.append(event)

    logger.info(
        f"Created {len(events)} CloudTrailEvent records affecting EC2 instances"
    )

    return events


@timeit
def load_cloudtrail_events(
    neo4j_session: neo4j.Session,
    events: list[dict[str, Any]],
    update_tag: int,
    account_id: str,
) -> None:
    """
    Load CloudTrailEvent nodes with relationships to SpaceliftRun and EC2Instance nodes.

    Uses standard node schema with other_relationships instead of MatchLinks for better performance.
    """
    logger.info(
        f"Loading {len(events)} CloudTrailEvent nodes with relationships into Neo4j"
    )

    load(
        neo4j_session,
        CloudTrailEventSchema(),
        events,
        lastupdated=update_tag,
        account_id=account_id,
    )

    logger.info(f"Successfully loaded {len(events)} CloudTrailEvent nodes")


@timeit
def cleanup_cloudtrail_events(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove stale CloudTrailEvent nodes and their relationships from Neo4j.

    Uses standard node schema cleanup - no MatchLink cleanup needed since we use other_relationships.
    """
    logger.debug("Running CloudTrailEvent cleanup job")

    GraphJob.from_node_schema(CloudTrailEventSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_ec2_ownership(
    neo4j_session: neo4j.Session,
    aws_session: boto3.Session,
    bucket_name: str,
    object_prefix: str,
    update_tag: int,
    account_id: str,
) -> None:
    """
    Sync EC2 ownership data from CloudTrail into Neo4j as CloudTrailEvent nodes.
    """
    logger.info("Starting EC2 ownership sync")

    cloudtrail_data = get_ec2_ownership(aws_session, bucket_name, object_prefix)

    events = transform_ec2_ownership(cloudtrail_data)

    if events:
        load_cloudtrail_events(neo4j_session, events, update_tag, account_id)
    else:
        logger.warning("No CloudTrail events found - no nodes created")

    # Cleanup stale data
    common_job_parameters = {
        "UPDATE_TAG": update_tag,
        "SPACELIFT_ACCOUNT_ID": account_id,
        "account_id": account_id,
    }
    cleanup_cloudtrail_events(neo4j_session, common_job_parameters)

    logger.info("EC2 ownership sync completed successfully")
