import json
import logging
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import boto3
import neo4j

from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_cloudtrail_events(
    boto3_session: boto3.Session, region: str, lookback_hours: int = 24
) -> List[Dict[str, Any]]:
    """
    Fetch CloudTrail management events from the specified time period.

    :type boto3_session: boto3.Session
    :param boto3_session: The boto3 session to use for API calls
    :type region: str
    :param region: The AWS region to fetch events from
    :type lookback_hours: int
    :param lookback_hours: Number of hours back to retrieve events from
    :rtype: List[Dict[str, Any]]
    :return: List of CloudTrail events
    """
    client = boto3_session.client(
        "cloudtrail", region_name=region, config=get_botocore_config()
    )

    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=lookback_hours)

    logger.info(
        f"Fetching CloudTrail management events for region '{region}' "
        f"from {start_time} to {end_time} ({lookback_hours} hours)"
    )

    events = []

    try:
        # Focus on STS events for role assumptions
        paginator = client.get_paginator("lookup_events")

        page_iterator = paginator.paginate(
            LookupAttributes=[
                {"AttributeKey": "EventSource", "AttributeValue": "sts.amazonaws.com"}
            ],
            StartTime=start_time,
            EndTime=end_time,
            PaginationConfig={
                "MaxItems": 10000,  # Reasonable limit to prevent excessive API calls
                "PageSize": 50,  # CloudTrail API limit per page
            },
        )

        for page in page_iterator:
            events.extend(page.get("Events", []))

        logger.info(
            f"Retrieved {len(events)} CloudTrail management events from region '{region}'"
        )

    except Exception as e:
        logger.warning(
            f"Failed to retrieve CloudTrail management events for region '{region}': {str(e)}"
        )

    return events


@timeit
def transform_cloudtrail_events_to_role_assumptions(
    events: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
) -> List[Dict[str, Any]]:
    """
    Transform raw CloudTrail events into role assumption relationships.

    :type events: List[Dict[str, Any]]
    :param events: List of raw CloudTrail events from lookup_events API
    :type region: str
    :param region: The AWS region where events were retrieved from
    :type current_aws_account_id: str
    :param current_aws_account_id: The AWS account ID being synced
    :rtype: List[Dict[str, Any]]
    :return: List of role assumption records in standardized format
    """
    role_assumptions = []

    logger.info(
        f"Transforming {len(events)} CloudTrail events to role assumptions for region '{region}'"
    )

    for event in events:
        try:
            assumption = _extract_role_assumption_from_event(
                event, region, current_aws_account_id
            )
            if assumption:
                role_assumptions.append(assumption)
        except Exception as e:
            logger.warning(
                f"Failed to transform CloudTrail event {event.get('EventId', 'unknown')}: {str(e)}"
            )
            continue

    logger.info(
        f"Successfully transformed {len(role_assumptions)} role assumptions from {len(events)} events"
    )
    return role_assumptions


@timeit
def load_role_assumptions(
    neo4j_session: neo4j.Session,
    role_assumptions: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load role assumption relationships into Neo4j using hybrid approach:
    - Uses AssumedRoleRel schema for structure and indexes
    - Uses raw Cypher for complex aggregation logic

    Creates direct ASSUMED_ROLE relationships with aggregated properties:
    (AWSUser|AWSRole|AWSPrincipal)-[:ASSUMED_ROLE {lastused, times_used, first_seen, last_seen}]->(AWSRole)

    :type neo4j_session: neo4j.Session
    :param neo4j_session: The Neo4j session to use for database operations
    :type role_assumptions: List[Dict[str, Any]]
    :param role_assumptions: List of role assumption records from transform function
    :type region: str
    :param region: The AWS region where events were retrieved from
    :type current_aws_account_id: str
    :param current_aws_account_id: The AWS account ID being synced
    :type aws_update_tag: int
    :param aws_update_tag: Timestamp tag for tracking data freshness
    :rtype: None
    """
    if not role_assumptions:
        logger.info("No role assumption events to load")
        return

    # Aggregate role assumptions by (source, destination) pairs
    aggregated_assumptions = _aggregate_role_assumptions(role_assumptions)

    logger.info(
        f"Loading {len(aggregated_assumptions)} aggregated role assumption relationships"
    )

    # Use raw Cypher for complex aggregation logic that cartography's query builder can't handle
    query = """
    UNWIND $assumptions AS assumption

    // Convert assumed role ARNs to IAM role ARNs for source matching
    WITH assumption,
         CASE
            WHEN assumption.source_principal_arn CONTAINS ':sts:' AND assumption.source_principal_arn CONTAINS 'assumed-role'
            THEN 'arn:aws:iam::' + split(assumption.source_principal_arn, ':')[4] + ':role/' + split(split(assumption.source_principal_arn, '/')[1], '/')[0]
            ELSE assumption.source_principal_arn
         END as source_role_arn

    // Find the source principal node (could be AWSUser, AWSRole, or AWSPrincipal)
    CALL {
        WITH source_role_arn
        MATCH (source:AWSUser {arn: source_role_arn})
        RETURN source as source_node
        UNION
        WITH source_role_arn
        MATCH (source:AWSRole {arn: source_role_arn})
        RETURN source as source_node
        UNION
        WITH source_role_arn
        MATCH (source:AWSPrincipal {arn: source_role_arn})
        RETURN source as source_node
    }

    // Find or create the destination role (handles cross-account roles)
    MERGE (dest:AWSRole {arn: assumption.destination_principal_arn})
    ON CREATE SET
        dest.name = split(split(assumption.destination_principal_arn, '/')[1], '/')[0],
        dest.accountid = split(assumption.destination_principal_arn, ':')[4],
        dest.created_time = datetime(),
        dest.lastupdated = $aws_update_tag
    ON MATCH SET
        dest.lastupdated = $aws_update_tag

    // Create or update the ASSUMED_ROLE relationship with aggregated properties
    MERGE (source_node)-[rel:ASSUMED_ROLE]->(dest)
    SET rel.lastused = COALESCE(
        CASE WHEN assumption.last_seen > COALESCE(rel.lastused, datetime('1970-01-01T00:00:00Z'))
        THEN assumption.last_seen
        ELSE rel.lastused END,
        assumption.last_seen
    ),
    rel.times_used = COALESCE(rel.times_used, 0) + assumption.times_used,
    rel.first_seen = COALESCE(
        CASE WHEN assumption.first_seen < COALESCE(rel.first_seen, datetime('2099-12-31T23:59:59Z'))
        THEN assumption.first_seen
        ELSE rel.first_seen END,
        assumption.first_seen
    ),
    rel.last_seen = COALESCE(
        CASE WHEN assumption.last_seen > COALESCE(rel.last_seen, datetime('1970-01-01T00:00:00Z'))
        THEN assumption.last_seen
        ELSE rel.last_seen END,
        assumption.last_seen
    ),
    rel.lastupdated = $aws_update_tag
    """

    """Executes the query"""
    neo4j_session.run(
        query,
        assumptions=aggregated_assumptions,
        aws_update_tag=aws_update_tag,
    )

    logger.info(
        f"Successfully loaded {len(aggregated_assumptions)} role assumption relationships"
    )


def _aggregate_role_assumptions(
    role_assumptions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Aggregate role assumption events by (source_principal, destination_principal) pairs.

    This creates the aggregated data needed for direct ASSUMED_ROLE relationships with
    properties like times_used, first_seen, last_seen, and lastused.

    :type role_assumptions: List[Dict[str, Any]]
    :param role_assumptions: List of individual role assumption records
    :rtype: List[Dict[str, Any]]
    :return: List of aggregated role assumption relationships
    """
    aggregated = {}

    for assumption in role_assumptions:
        source_arn = assumption.get("SourcePrincipal")
        dest_arn = assumption.get("DestinationPrincipal")
        event_time = assumption.get("EventTime")

        if not source_arn or not dest_arn or not event_time:
            logger.warning(
                "Skipping incomplete assumption record: due to missing required fields"
            )
            continue

        # Create aggregation key
        key = (source_arn, dest_arn)

        if key not in aggregated:
            aggregated[key] = {
                "source_principal_arn": source_arn,
                "destination_principal_arn": dest_arn,
                "times_used": 1,
                "first_seen": event_time,
                "last_seen": event_time,
            }
        else:
            # Update aggregated values
            agg_data = aggregated[key]
            agg_data["times_used"] += 1

            # Update temporal bounds
            if event_time < agg_data["first_seen"]:
                agg_data["first_seen"] = event_time
            if event_time > agg_data["last_seen"]:
                agg_data["last_seen"] = event_time

    # Convert to list and ensure lastused equals last_seen
    result = []
    for agg_data in aggregated.values():
        agg_data["lastused"] = agg_data["last_seen"]
        result.append(agg_data)

    logger.info(
        f"Aggregated {len(role_assumptions)} events into {len(result)} unique role assumption relationships"
    )
    return result


def _extract_role_assumption_from_event(
    event: Dict[str, Any],
    region: str,
    current_aws_account_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Extract role assumption details from a single CloudTrail event.

    :type event: Dict[str, Any]
    :param event: Single CloudTrail event from lookup_events API
    :type region: str
    :param region: The AWS region where the event occurred
    :type current_aws_account_id: str
    :param current_aws_account_id: The AWS account ID being synced
    :rtype: Optional[Dict[str, Any]]
    :return: Role assumption record or None if event is not a role assumption
    """
    event_name = event.get("EventName")

    # Only process STS role assumption events
    if event_name not in [
        "AssumeRole",
        "AssumeRoleWithSAML",
        "AssumeRoleWithWebIdentity",
    ]:
        return None

    # Extract source principal (who is assuming the role)
    source_principal = _extract_source_principal(event)
    if not source_principal:
        logger.debug(
            f"Could not extract source principal from event {event.get('EventId')}"
        )
        return None

    # Extract destination principal (role being assumed)
    destination_principal = _extract_destination_principal(event)
    if not destination_principal:
        logger.debug(
            f"Could not extract destination principal from event {event.get('EventId')}"
        )
        return None

    # Build the standardized role assumption record
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
    }

    # Add additional context from CloudTrail event JSON
    cloudtrail_event = _parse_cloudtrail_event_json(event.get("CloudTrailEvent"))
    if cloudtrail_event:
        assumption.update(
            {
                "SessionName": _extract_session_name(cloudtrail_event, event_name),
                "RequestId": cloudtrail_event.get("requestID"),
                "RecipientAccountId": cloudtrail_event.get("recipientAccountId"),
            }
        )

    return assumption


def _extract_source_principal(event: Dict[str, Any]) -> Optional[str]:
    """Extract the source principal (who is assuming the role) from a CloudTrail event."""
    user_identity = event.get("UserIdentity", {})

    # Try to get ARN from UserIdentity
    if user_identity.get("arn"):
        return user_identity["arn"]

    # For SAML users, construct ARN from available info
    if user_identity.get("type") == "SAMLUser":
        principal_id = user_identity.get("principalId")
        if principal_id:
            return principal_id

    # For Web Identity users, use the assumed role ARN if available
    if user_identity.get("type") == "WebIdentityUser":
        return user_identity.get("arn")

    # Fallback to UserName if available
    user_name = event.get("UserName")
    if user_name:
        return user_name

    # For AWS service role assumptions, UserIdentity is often empty
    # Try to extract source from CloudTrail event JSON
    cloudtrail_event = _parse_cloudtrail_event_json(event.get("CloudTrailEvent"))
    if cloudtrail_event:
        # Check for source identity in userIdentity field of CloudTrail JSON
        ct_user_identity = cloudtrail_event.get("userIdentity", {})
        if ct_user_identity.get("arn"):
            return ct_user_identity["arn"]

        # For AWS service calls, the source is often the service itself
        if ct_user_identity.get("type") == "AWSService":
            service_name = ct_user_identity.get("invokedBy")
            if service_name:
                # Return the service as the source principal
                return f"service:{service_name}"

        # Check if this is a service-linked role assumption
        # In this case, we can use the account root as the source
        account_id = cloudtrail_event.get("recipientAccountId")
        if account_id and ct_user_identity.get("type") in ["Root", "AWSAccount"]:
            return f"arn:aws:iam::{account_id}:root"

    return None


def _extract_destination_principal(event: Dict[str, Any]) -> Optional[str]:
    """Extract the destination principal (role being assumed) from a CloudTrail event."""
    # Parse the CloudTrail event JSON for detailed information
    cloudtrail_event = _parse_cloudtrail_event_json(event.get("CloudTrailEvent"))
    if not cloudtrail_event:
        return None

    # Extract role ARN from request parameters
    request_params = cloudtrail_event.get("requestParameters", {})
    role_arn = request_params.get("roleArn")

    if role_arn:
        return role_arn

    # Fallback: try to extract from response elements for some STS calls
    response_elements = cloudtrail_event.get("responseElements", {})
    assumed_role_user = response_elements.get("assumedRoleUser", {})
    if assumed_role_user.get("arn"):
        # Convert assumed role ARN back to role ARN
        # e.g., "arn:aws:sts::123456789012:assumed-role/MyRole/session" -> "arn:aws:iam::123456789012:role/MyRole"
        assumed_role_arn = assumed_role_user["arn"]
        return _convert_assumed_role_arn_to_role_arn(assumed_role_arn)

    return None


def _extract_session_name(
    cloudtrail_event: Dict[str, Any], event_name: str
) -> Optional[str]:
    """Extract the role session name from CloudTrail event details."""
    request_params = cloudtrail_event.get("requestParameters", {})
    return request_params.get("roleSessionName")


def _parse_cloudtrail_event_json(
    cloudtrail_event_str: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Parse the CloudTrail event JSON string into a dictionary."""
    if not cloudtrail_event_str:
        return None

    try:
        return json.loads(cloudtrail_event_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.debug(f"Failed to parse CloudTrail event JSON: {str(e)}")
        return None


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
    1. Fetch CloudTrail management events from all regions
    2. Transform events into role assumption records
    3. Load aggregated role assumption relationships into Neo4j

    The resulting graph contains direct relationships like:
    (AWSUser|AWSRole|AWSPrincipal)-[:ASSUMED_ROLE {times_used, first_seen, last_seen, lastused}]->(AWSRole)

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

    all_role_assumptions = []

    # Fetch events from all regions
    for region in regions:
        try:
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

            all_role_assumptions.extend(role_assumptions)

        except Exception as e:
            logger.warning(
                f"Failed to process CloudTrail events for region {region}: {str(e)}"
            )
            continue

    # Load all role assumptions into Neo4j
    if all_role_assumptions:
        load_role_assumptions(
            neo4j_session=neo4j_session,
            role_assumptions=all_role_assumptions,
            region="all",  # Indicates cross-region aggregation
            current_aws_account_id=current_aws_account_id,
            aws_update_tag=update_tag,
        )

        logger.info(
            f"CloudTrail management events sync completed successfully. "
            f"Processed {len(all_role_assumptions)} role assumption events."
        )
    else:
        logger.info(
            "CloudTrail management events sync completed - no role assumptions found"
        )
