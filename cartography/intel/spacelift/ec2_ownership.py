import json
import logging
import re
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load_matchlinks
from cartography.models.spacelift.run import SpaceliftRunToEC2InstanceMatchLinkRel
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Regex pattern to match EC2 instance IDs
INSTANCE_ID_PATTERN = re.compile(r"\b(i-[0-9a-f]{8,17})\b")


@aws_handle_regions
@timeit
def get_ec2_ownership(
    aws_session: boto3.Session, bucket_name: str, object_key: str
) -> list[dict[str, Any]]:
    """
    Fetch EC2 ownership data from S3 bucket containing Athena query results.
    """
    logger.info(f"Fetching EC2 ownership data from s3://{bucket_name}/{object_key}")

    # Create S3 client from the boto3 session
    s3_client = aws_session.client("s3")

    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)

    object_body = response["Body"].read()

    # Decode bytes to string and parse JSON
    json_content = json.loads(object_body.decode("utf-8"))

    logger.info("Successfully fetched and parsed EC2 ownership data from S3")

    return json_content


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
    Transform CloudTrail data to map Spacelift run IDs to EC2 instance IDs.

    This function filters CloudTrail records to find those that have BOTH:
    1. A Spacelift run ID (from the useridentity field)
    2. An EC2 instance ID (from resources, requestparameters, or responseelements)
    """
    logger.info(
        f"Transforming {len(cloudtrail_data)} CloudTrail records to map Spacelift runs to EC2 instances"
    )

    mappings = []

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

        # Create a mapping for each run_id -> instance_id pair
        for instance_id in instance_ids:
            mapping = {
                "run_id": run_id,
                "instance_id": instance_id,
                "event_time": record.get("eventtime"),
                "event_name": record.get("eventname"),
                "aws_account": record.get("account"),
                "aws_region": record.get("awsregion"),
            }
            mappings.append(mapping)

    logger.info(f"Found {len(mappings)} Spacelift run -> EC2 instance mappings")

    return mappings


@timeit
def load_ec2_ownership_relationships(
    neo4j_session: neo4j.Session,
    mappings: list[dict[str, Any]],
    update_tag: int,
    account_id: str,
) -> None:
    """
    Load AFFECTED relationships between SpaceliftRun and EC2Instance nodes using MatchLink.
    """
    logger.info(f"Loading {len(mappings)} EC2 ownership relationships into Neo4j")

    load_matchlinks(
        neo4j_session,
        SpaceliftRunToEC2InstanceMatchLinkRel(),
        mappings,
        lastupdated=update_tag,
        _sub_resource_label="SpaceliftAccount",
        _sub_resource_id=account_id,
    )

    logger.info(f"Successfully loaded {len(mappings)} EC2 ownership relationships")


@timeit
def sync_ec2_ownership(
    neo4j_session: neo4j.Session,
    aws_session: boto3.Session,
    bucket_name: str,
    object_key: str,
    update_tag: int,
    account_id: str,
) -> None:

    logger.info("Starting EC2 ownership sync")

    cloudtrail_data = get_ec2_ownership(aws_session, bucket_name, object_key)

    mappings = transform_ec2_ownership(cloudtrail_data)

    if mappings:
        load_ec2_ownership_relationships(
            neo4j_session, mappings, update_tag, account_id
        )
    else:
        logger.warning("No EC2 ownership mappings found - no relationships created")

    logger.info("EC2 ownership sync completed successfully")
