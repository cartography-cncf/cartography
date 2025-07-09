import json
import logging
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.cloudtrail.management_events import AssumedRoleMatchLink
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_cloudtrail_events(
    boto3_session: boto3.Session, region: str, lookback_hours: int = 24
) -> List[Dict[str, Any]]:
    """
    Fetch CloudTrail role assumption events from the specified time period.

    Makes separate API calls for each role assumption event type to minimize
    data transfer and processing overhead.

    :type boto3_session: boto3.Session
    :param boto3_session: The boto3 session to use for API calls
    :type region: str
    :param region: The AWS region to fetch events from
    :type lookback_hours: int
    :param lookback_hours: Number of hours back to retrieve events from
    :rtype: List[Dict[str, Any]]
    :return: List of CloudTrail role assumption events
    """
    client = boto3_session.client(
        "cloudtrail", region_name=region, config=get_botocore_config()
    )

    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=lookback_hours)

    logger.info(
        f"Fetching CloudTrail role assumption events for region '{region}' "
        f"from {start_time} to {end_time} ({lookback_hours} hours)"
    )

    # Specific STS events for role assumptions
    role_assumption_events = [
        "AssumeRole",
        "AssumeRoleWithSAML",
        "AssumeRoleWithWebIdentity",
    ]

    all_events = []
    paginator = client.get_paginator("lookup_events")

    # Make separate API calls for each event type
    for event_name in role_assumption_events:
        logger.debug(f"Fetching {event_name} events for region '{region}'")

        page_iterator = paginator.paginate(
            LookupAttributes=[
                {"AttributeKey": "EventName", "AttributeValue": event_name}
            ],
            StartTime=start_time,
            EndTime=end_time,
            PaginationConfig={
                "MaxItems": 10000,  # Reasonable limit to prevent excessive API calls
                "PageSize": 50,  # CloudTrail API limit per page
            },
        )

        events_for_type = []
        for page in page_iterator:
            events_for_type.extend(page.get("Events", []))

        logger.debug(
            f"Retrieved {len(events_for_type)} {event_name} events from region '{region}'"
        )
        all_events.extend(events_for_type)

    logger.info(
        f"Retrieved {len(all_events)} total role assumption events from region '{region}'"
    )

    return all_events


@timeit
def transform_cloudtrail_events_to_role_assumptions(
    events: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
) -> List[Dict[str, Any]]:
    """
    Transform raw CloudTrail events into aggregated role assumption relationships.

    This function performs the complete transformation pipeline:
    1. Extract role assumption events from CloudTrail data
    2. Aggregate events by (source_principal, destination_principal) pairs
    3. Return aggregated relationships ready for loading

    :type events: List[Dict[str, Any]]
    :param events: List of raw CloudTrail events from lookup_events API
    :type region: str
    :param region: The AWS region where events were retrieved from
    :type current_aws_account_id: str
    :param current_aws_account_id: The AWS account ID being synced
    :rtype: List[Dict[str, Any]]
    :return: List of aggregated role assumption relationships ready for loading
    """
    role_assumptions = []

    logger.info(
        f"Transforming {len(events)} CloudTrail events to role assumptions for region '{region}'"
    )

    for event in events:
        # Extract role assumption details from CloudTrail event
        event_name = event.get("EventName")
        if not event_name:
            logger.debug(
                f"Event missing EventName field: {event.get('EventId', 'unknown')}"
            )
            continue

        # Parse CloudTrail event JSON once
        cloudtrail_event = None
        if event.get("CloudTrailEvent"):
            try:
                cloudtrail_event = json.loads(event["CloudTrailEvent"])
            except (json.JSONDecodeError, TypeError):
                logger.debug(
                    f"Failed to parse CloudTrail JSON for event {event.get('EventId', 'unknown')}"
                )

        # Simple source principal extraction
        user_identity = event.get("UserIdentity", {})
        source_principal = (
            user_identity.get("arn")
            or user_identity.get("principalId")
            or event.get("UserName")
            or (
                cloudtrail_event and cloudtrail_event.get("userIdentity", {}).get("arn")
            )
        )

        if not source_principal:
            logger.debug(
                f"Could not extract source principal from event {event.get('EventId', 'unknown')}"
            )
            continue

        # Simple destination principal extraction
        destination_principal = None
        if cloudtrail_event:
            # Try request parameters first
            destination_principal = cloudtrail_event.get("requestParameters", {}).get(
                "roleArn"
            )

            # Fallback: try response elements
            if not destination_principal:
                assumed_role_arn = (
                    cloudtrail_event.get("responseElements", {})
                    .get("assumedRoleUser", {})
                    .get("arn")
                )
                if assumed_role_arn:
                    destination_principal = _convert_assumed_role_arn_to_role_arn(
                        assumed_role_arn
                    )

        if not destination_principal:
            logger.debug(
                f"Could not extract destination principal from event {event.get('EventId', 'unknown')}"
            )
            continue

        # Create standardized role assumption record
        assumption = {
            "SourcePrincipal": source_principal,
            "DestinationPrincipal": destination_principal,
            "Action": event_name,
            "EventId": event.get("EventId"),
            "EventTime": event.get("EventTime"),
            "SourceIPAddress": event.get("SourceIPAddress"),
            "UserAgent": event.get("UserAgent"),
            "AwsRegion": event.get("AwsRegion", region),
            "AccountId": current_aws_account_id,
            "AssumedRoleArn": destination_principal,  # For relationship targeting
            "PrincipalArn": source_principal,  # For relationship targeting
            "SessionName": cloudtrail_event
            and cloudtrail_event.get("requestParameters", {}).get("roleSessionName"),
            "RequestId": cloudtrail_event and cloudtrail_event.get("requestID"),
            "RecipientAccountId": cloudtrail_event
            and cloudtrail_event.get("recipientAccountId"),
        }
        role_assumptions.append(assumption)

    logger.info(
        f"Successfully transformed {len(role_assumptions)} role assumptions from {len(events)} events"
    )

    # Aggregate role assumptions by (source, destination) pairs
    aggregated_assumptions = _aggregate_role_assumptions(role_assumptions)

    return aggregated_assumptions


@timeit
def load_role_assumptions(
    neo4j_session: neo4j.Session,
    aggregated_role_assumptions: List[Dict[str, Any]],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load aggregated role assumption relationships into Neo4j using MatchLink pattern.

    Creates direct ASSUMED_ROLE relationships with aggregated properties:
    (AWSUser|AWSRole|AWSPrincipal)-[:ASSUMED_ROLE {lastused, times_used, first_seen, last_seen}]->(AWSRole)

    Assumes that both source principals and destination roles already exist in the graph.

    :type neo4j_session: neo4j.Session
    :param neo4j_session: The Neo4j session to use for database operations
    :type aggregated_role_assumptions: List[Dict[str, Any]]
    :param aggregated_role_assumptions: List of aggregated role assumption relationships from transform function
    :type current_aws_account_id: str
    :param current_aws_account_id: The AWS account ID being synced
    :type aws_update_tag: int
    :param aws_update_tag: Timestamp tag for tracking data freshness
    :rtype: None
    """
    # Use MatchLink to create relationships between existing nodes
    matchlink_schema = AssumedRoleMatchLink()

    load_matchlinks(
        neo4j_session,
        matchlink_schema,
        aggregated_role_assumptions,
        lastupdated=aws_update_tag,
        _sub_resource_label="AWSAccount",
        _sub_resource_id=current_aws_account_id,
    )

    logger.info(
        f"Successfully loaded {len(aggregated_role_assumptions)} role assumption relationships"
    )


def _aggregate_role_assumptions(
    role_assumptions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Aggregate role assumption events by (source_arn, destination_arn) pairs.

    Combines multiple assumption events between the same source and destination
    into a single record.

    :param role_assumptions: List of role assumption events
    :return: List of aggregated role assumption records
    """
    aggregated: Dict[tuple, Dict[str, Any]] = {}

    for assumption in role_assumptions:
        source_arn = assumption.get("SourcePrincipal")
        dest_arn = assumption.get("DestinationPrincipal")
        event_time = assumption.get("EventTime")

        missing_fields = []
        if not source_arn:
            missing_fields.append("SourcePrincipal")
        if not dest_arn:
            missing_fields.append("DestinationPrincipal")
        if not event_time:
            missing_fields.append("EventTime")

        if missing_fields:
            logger.warning(
                f"Skipping incomplete assumption record missing: {', '.join(missing_fields)}"
            )
            continue

        # MyPy check is forcing this assert check because it thinks source_arn could be None. Could do a more explicit check above if this is a problem.
        assert source_arn is not None
        # Convert STS assumed-role ARNs to IAM role ARNs for source matching
        normalized_source_arn = _convert_assumed_role_arn_to_role_arn(source_arn)

        # Create aggregation key
        key = (normalized_source_arn, dest_arn)

        if key in aggregated:
            # Update aggregated values
            agg_data = aggregated[key]
            agg_data["times_used"] += 1

            # Update temporal bounds
            if event_time < agg_data["first_seen"]:
                agg_data["first_seen"] = event_time
            if event_time > agg_data["last_used"]:
                agg_data["last_used"] = event_time
        else:
            aggregated[key] = {
                "source_principal_arn": normalized_source_arn,
                "destination_principal_arn": dest_arn,
                "times_used": 1,
                "first_seen": event_time,
                "last_used": event_time,
            }

    return list(aggregated.values())


def _convert_assumed_role_arn_to_role_arn(assumed_role_arn: str) -> str:
    """
    Convert an assumed role ARN to the original role ARN.

    Example:
    Input:  "arn:aws:sts::123456789012:assumed-role/MyRole/session-name"
    Output: "arn:aws:iam::123456789012:role/MyRole"
    """
    try:
        # Split the ARN into parts
        arn_parts = assumed_role_arn.split(":")
        if (
            len(arn_parts) >= 6
            and arn_parts[2] == "sts"
            and "assumed-role" in arn_parts[5]
        ):
            # Extract account ID and role name
            account_id = arn_parts[4]
            resource_part = arn_parts[5]  # "assumed-role/MyRole/session-name"
            role_name = resource_part.split("/")[1]  # Extract "MyRole"

            # Construct the IAM role ARN
            return f"arn:aws:iam::{account_id}:role/{role_name}"
    except (IndexError, AttributeError):
        logger.debug(
            f"Could not convert assumed role ARN to role ARN: {assumed_role_arn}"
        )

    # Return original ARN if conversion fails
    return assumed_role_arn


@timeit
def cleanup(
    neo4j_session: neo4j.Session, current_aws_account_id: str, update_tag: int
) -> None:
    """
    Run CloudTrail management events cleanup job to remove stale ASSUMED_ROLE relationships.

    :type neo4j_session: neo4j.Session
    :param neo4j_session: The Neo4j session to use for database operations
    :type current_aws_account_id: str
    :param current_aws_account_id: The AWS account ID being synced
    :type update_tag: int
    :param update_tag: Timestamp tag for tracking data freshness
    :rtype: None
    """
    logger.debug("Running CloudTrail management events cleanup job.")

    matchlink_schema = AssumedRoleMatchLink()
    cleanup_job = GraphJob.from_matchlink(
        matchlink_schema,
        "AWSAccount",
        current_aws_account_id,
        update_tag,
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync CloudTrail management events to create ASSUMED_ROLE relationships.

    This function orchestrates the complete process:
    1. Fetch CloudTrail management events region by region
    2. Transform events into role assumption records per region
    3. Load role assumption relationships into Neo4j for each region
    4. Run cleanup after processing all regions

    The resulting graph contains direct relationships like:
    (AWSUser|AWSRole|AWSPrincipal)-[:ASSUMED_ROLE {times_used, first_seen, last_used, lastused}]->(AWSRole)

    :type neo4j_session: neo4j.Session
    :param neo4j_session: The Neo4j session
    :type boto3_session: boto3.Session
    :param boto3_session: The boto3 session to use for API calls
    :type regions: List[str]
    :param regions: List of AWS regions to sync
    :type current_aws_account_id: str
    :param current_aws_account_id: The AWS account ID being synced
    :type aws_update_tag: int
    :param aws_update_tag: Timestamp tag for tracking data freshness
    :rtype: None
    """
    # Extract lookback hours from common_job_parameters (set by CLI parameter)
    lookback_hours = common_job_parameters.get(
        "aws_cloudtrail_management_events_lookback_hours"
    )

    if not lookback_hours:
        logger.info(
            "CloudTrail management events sync skipped - no lookback period specified"
        )
        return

    logger.info(
        f"Starting CloudTrail management events sync for account {current_aws_account_id}"
    )
    logger.info(
        f"Syncing {len(regions)} regions with {lookback_hours} hour lookback period"
    )

    total_role_assumptions = 0

    # Process events region by region
    for region in regions:
        logger.info(f"Processing CloudTrail events for region {region}")

        # Get raw CloudTrail events
        events = get_cloudtrail_events(
            boto3_session=boto3_session,
            region=region,
            lookback_hours=lookback_hours,
        )

        # Transform to role assumptions
        role_assumptions = transform_cloudtrail_events_to_role_assumptions(
            events=events,
            region=region,
            current_aws_account_id=current_aws_account_id,
        )

        # Load role assumptions for this region
        load_role_assumptions(
            neo4j_session=neo4j_session,
            aggregated_role_assumptions=role_assumptions,
            current_aws_account_id=current_aws_account_id,
            aws_update_tag=update_tag,
        )
        total_role_assumptions += len(role_assumptions)
        logger.info(
            f"Loaded {len(role_assumptions)} role assumptions for region {region}"
        )

    # Run cleanup for stale relationships after processing all regions
    cleanup(neo4j_session, current_aws_account_id, update_tag)

    logger.info(
        f"CloudTrail management events sync completed successfully. "
        f"Processed {total_role_assumptions} total role assumption events across {len(regions)} regions."
    )
