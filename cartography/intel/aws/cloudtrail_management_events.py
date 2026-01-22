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
from cartography.models.aws.cloudtrail.management_events import (
    AssumedRoleWithSAMLMatchLink,
)
from cartography.models.aws.cloudtrail.management_events import (
    GitHubRepoAssumeRoleWithWebIdentityMatchLink,
)
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_assume_role_events(
    boto3_session: boto3.Session, region: str, lookback_hours: int
) -> List[Dict[str, Any]]:
    """
    Fetch CloudTrail AssumeRole events from the specified time period.

    Focuses specifically on standard AssumeRole events, excluding SAML and WebIdentity variants.

    :type boto3_session: boto3.Session
    :param boto3_session: The boto3 session to use for API calls
    :type region: str
    :param region: The AWS region to fetch events from
    :type lookback_hours: int
    :param lookback_hours: Number of hours back to retrieve events from
    :rtype: List[Dict[str, Any]]
    :return: List of CloudTrail AssumeRole events
    """
    client = boto3_session.client(
        "cloudtrail", region_name=region, config=get_botocore_config()
    )

    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=lookback_hours)

    logger.info(
        f"Fetching CloudTrail AssumeRole events for region '{region}' "
        f"from {start_time} to {end_time} ({lookback_hours} hours)"
    )

    paginator = client.get_paginator("lookup_events")

    page_iterator = paginator.paginate(
        LookupAttributes=[
            {"AttributeKey": "EventName", "AttributeValue": "AssumeRole"}
        ],
        StartTime=start_time,
        EndTime=end_time,
        PaginationConfig={
            "MaxItems": 10000,  # Reasonable limit to prevent excessive API calls
            "PageSize": 50,  # CloudTrail API limit per page
        },
    )

    all_events = []
    for page in page_iterator:
        all_events.extend(page.get("Events", []))

    logger.info(f"Retrieved {len(all_events)} AssumeRole events from region '{region}'")

    return all_events


@timeit
@aws_handle_regions
def get_saml_role_events(
    boto3_session: boto3.Session, region: str, lookback_hours: int
) -> List[Dict[str, Any]]:
    """
    Fetch CloudTrail AssumeRoleWithSAML events from the specified time period.

    Focuses specifically on SAML-based role assumption events.

    :type boto3_session: boto3.Session
    :param boto3_session: The boto3 session to use for API calls
    :type region: str
    :param region: The AWS region to fetch events from
    :type lookback_hours: int
    :param lookback_hours: Number of hours back to retrieve events from
    :rtype: List[Dict[str, Any]]
    :return: List of CloudTrail AssumeRoleWithSAML events
    """
    client = boto3_session.client(
        "cloudtrail", region_name=region, config=get_botocore_config()
    )

    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=lookback_hours)

    logger.info(
        f"Fetching CloudTrail AssumeRoleWithSAML events for region '{region}' "
        f"from {start_time} to {end_time} ({lookback_hours} hours)"
    )

    paginator = client.get_paginator("lookup_events")

    page_iterator = paginator.paginate(
        LookupAttributes=[
            {"AttributeKey": "EventName", "AttributeValue": "AssumeRoleWithSAML"}
        ],
        StartTime=start_time,
        EndTime=end_time,
        PaginationConfig={
            "MaxItems": 10000,  # Reasonable limit to prevent excessive API calls
            "PageSize": 50,  # CloudTrail API limit per page
        },
    )

    all_events = []
    for page in page_iterator:
        all_events.extend(page.get("Events", []))

    logger.info(
        f"Retrieved {len(all_events)} AssumeRoleWithSAML events from region '{region}'"
    )

    return all_events


@timeit
@aws_handle_regions
def get_web_identity_role_events(
    boto3_session: boto3.Session, region: str, lookback_hours: int
) -> List[Dict[str, Any]]:
    """
    Fetch CloudTrail AssumeRoleWithWebIdentity events from the specified time period.

    Focuses specifically on WebIdentity-based role assumption events.

    :type boto3_session: boto3.Session
    :param boto3_session: The boto3 session to use for API calls
    :type region: str
    :param region: The AWS region to fetch events from
    :type lookback_hours: int
    :param lookback_hours: Number of hours back to retrieve events from
    :rtype: List[Dict[str, Any]]
    :return: List of CloudTrail AssumeRoleWithWebIdentity events
    """
    client = boto3_session.client(
        "cloudtrail", region_name=region, config=get_botocore_config()
    )

    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=lookback_hours)

    logger.info(
        f"Fetching CloudTrail AssumeRoleWithWebIdentity events for region '{region}' "
        f"from {start_time} to {end_time} ({lookback_hours} hours)"
    )

    paginator = client.get_paginator("lookup_events")

    page_iterator = paginator.paginate(
        LookupAttributes=[
            {"AttributeKey": "EventName", "AttributeValue": "AssumeRoleWithWebIdentity"}
        ],
        StartTime=start_time,
        EndTime=end_time,
        PaginationConfig={
            "MaxItems": 10000,  # Reasonable limit to prevent excessive API calls
            "PageSize": 50,  # CloudTrail API limit per page
        },
    )

    all_events = []
    for page in page_iterator:
        all_events.extend(page.get("Events", []))

    logger.info(
        f"Retrieved {len(all_events)} AssumeRoleWithWebIdentity events from region '{region}'"
    )

    return all_events


@timeit
def transform_assume_role_events_to_role_assumptions(
    events: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Transform raw CloudTrail AssumeRole events into aggregated role assumption relationships.

    Focuses specifically on standard AssumeRole events, providing optimized processing
    for the most common role assumption scenario.

    This function performs the complete transformation pipeline:
    1. Extract role assumption events from CloudTrail AssumeRole data
    2. Aggregate events by (source_principal, destination_principal) pairs
    3. Return aggregated relationships ready for loading

    :type events: List[Dict[str, Any]]
    :param events: List of raw CloudTrail AssumeRole events from lookup_events API
    :rtype: List[Dict[str, Any]]
    :return: List of aggregated role assumption relationships ready for loading
    """
    aggregated: Dict[tuple, Dict[str, Any]] = {}
    logger.info(
        f"Transforming {len(events)} CloudTrail AssumeRole events to role assumptions"
    )

    for event in events:

        cloudtrail_event = json.loads(event["CloudTrailEvent"])

        # Skip events with null requestParameters since we can't extract roleArn
        if not cloudtrail_event.get("requestParameters"):
            logger.debug(
                f"Skipping CloudTrail AssumeRole event due to missing requestParameters. Event: {event.get('EventId', 'unknown')}"
            )
            continue

        if cloudtrail_event.get("userIdentity", {}).get("arn"):
            source_principal = cloudtrail_event["userIdentity"]["arn"]
            destination_principal = cloudtrail_event["requestParameters"]["roleArn"]
        else:
            logger.debug(
                f"Skipping CloudTrail AssumeRole event due to missing UserIdentity.arn. Event: {event.get('EventId', 'unknown')}"
            )
            continue

        destination_principal = cloudtrail_event["requestParameters"]["roleArn"]

        normalized_source_principal = _convert_assumed_role_arn_to_role_arn(
            source_principal
        )
        normalized_destination_principal = _convert_assumed_role_arn_to_role_arn(
            destination_principal
        )
        event_time = event.get("EventTime")

        key = (normalized_source_principal, normalized_destination_principal)

        if key in aggregated:
            aggregated[key]["times_used"] += 1
            # Handle None values safely for time comparisons
            if event_time:
                existing_first = aggregated[key]["first_seen_in_time_window"]
                existing_last = aggregated[key]["last_used"]

                if existing_first is None or event_time < existing_first:
                    aggregated[key]["first_seen_in_time_window"] = event_time
                if existing_last is None or event_time > existing_last:
                    aggregated[key]["last_used"] = event_time
        else:
            aggregated[key] = {
                "source_principal_arn": normalized_source_principal,
                "destination_principal_arn": normalized_destination_principal,
                "times_used": 1,
                "first_seen_in_time_window": event_time,
                "last_used": event_time,
            }

    return list(aggregated.values())


@timeit
def transform_saml_role_events_to_role_assumptions(
    events: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Transform raw CloudTrail AssumeRoleWithSAML events into aggregated role assumption relationships.

    Focuses specifically on SAML-based role assumption events, providing optimized processing
    for federated identity scenarios.

    This function performs the complete transformation pipeline:
    1. Extract role assumption events from CloudTrail AssumeRoleWithSAML data
    2. Aggregate events by (source_principal, destination_principal) pairs
    3. Return aggregated relationships ready for loading

    :type events: List[Dict[str, Any]]
    :param events: List of raw CloudTrail AssumeRoleWithSAML events from lookup_events API
    :rtype: List[Dict[str, Any]]
    :return: List of aggregated SAML role assumption relationships ready for loading.
             Each dict contains keys: source_principal_arn, destination_principal_arn,
             times_used, first_seen_in_time_window, last_used
    """
    aggregated: Dict[tuple, Dict[str, Any]] = {}
    logger.info(
        f"Transforming {len(events)} CloudTrail AssumeRoleWithSAML events to role assumptions"
    )

    for event in events:

        cloudtrail_event = json.loads(event["CloudTrailEvent"])

        # Skip events with null requestParameters since we can't extract roleArn
        if not cloudtrail_event.get("requestParameters"):
            logger.debug(
                f"Skipping CloudTrail AssumeRoleWithSAML event due to missing requestParameters. Event: {event.get('EventId', 'unknown')}"
            )
            continue

        response_elements = cloudtrail_event.get("responseElements", {})
        assumed_role_user = response_elements.get("assumedRoleUser", {})

        if assumed_role_user.get("arn"):
            assumed_role_arn = assumed_role_user["arn"]
            # Extract username from assumed role ARN: arn:aws:sts::account:assumed-role/RoleName/username
            source_principal = assumed_role_arn.split("/")[-1]
            destination_principal = cloudtrail_event["requestParameters"]["roleArn"]
        else:
            logger.debug(
                f"Skipping CloudTrail AssumeRoleWithSAML event due to missing assumedRoleUser.arn. Event: {event.get('EventId', 'unknown')}"
            )
            continue

        event_time = event.get("EventTime")

        key = (source_principal, destination_principal)

        if key in aggregated:
            aggregated[key]["times_used"] += 1
            # Handle None values safely for time comparisons
            if event_time:
                existing_first = aggregated[key]["first_seen_in_time_window"]
                existing_last = aggregated[key]["last_used"]

                if existing_first is None or event_time < existing_first:
                    aggregated[key]["first_seen_in_time_window"] = event_time
                if existing_last is None or event_time > existing_last:
                    aggregated[key]["last_used"] = event_time
        else:
            aggregated[key] = {
                "source_principal_arn": source_principal,
                "destination_principal_arn": destination_principal,
                "times_used": 1,
                "first_seen_in_time_window": event_time,
                "last_used": event_time,
            }

    return list(aggregated.values())


@timeit
def transform_web_identity_role_events_to_role_assumptions(
    events: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Transform raw CloudTrail AssumeRoleWithWebIdentity events into aggregated role assumption relationships.

    Focuses specifically on WebIdentity-based role assumption events, providing optimized processing
    for federated web identity scenarios.

    This function performs the complete transformation pipeline:
    1. Extract role assumption events from CloudTrail AssumeRoleWithWebIdentity data
    2. Aggregate events by (source_principal, destination_principal) pairs
    3. Return aggregated relationships ready for loading

    :type events: List[Dict[str, Any]]
    :param events: List of raw CloudTrail AssumeRoleWithWebIdentity events from lookup_events API
    :rtype: List[Dict[str, Any]]
    :return: List of aggregated WebIdentity role assumption relationships ready for loading.
             Each dict contains keys: source_repo_fullname, destination_principal_arn,
             times_used, first_seen_in_time_window, last_used
    """
    github_aggregated: Dict[tuple, Dict[str, Any]] = {}
    logger.info(
        f"Transforming {len(events)} CloudTrail AssumeRoleWithWebIdentity events to role assumptions"
    )

    for event in events:

        cloudtrail_event = json.loads(event["CloudTrailEvent"])

        # Skip events with null requestParameters since we can't extract roleArn
        if not cloudtrail_event.get("requestParameters"):
            logger.debug(
                f"Skipping CloudTrail AssumeRoleWithWebIdentity event due to missing requestParameters. Event: {event.get('EventId', 'unknown')}"
            )
            continue

        user_identity = cloudtrail_event.get("userIdentity", {})

        if user_identity.get("type") == "WebIdentityUser" and user_identity.get(
            "userName"
        ):
            identity_provider = user_identity.get("identityProvider", "unknown")
            destination_principal = cloudtrail_event["requestParameters"]["roleArn"]
            event_time = event.get("EventTime")

            # Only process GitHub Actions events
            if "token.actions.githubusercontent.com" in identity_provider:
                # Extract GitHub repo fullname from userName format: "repo:{organization}/{repository}:{context}"
                user_name = user_identity.get("userName", "")
                if not user_name:
                    logger.debug(
                        f"Missing userName in GitHub WebIdentity event: {event.get('EventId', 'unknown')}"
                    )
                    continue

                github_repo = _extract_github_repo_from_username(user_name)
                key = (github_repo, destination_principal)

                if key in github_aggregated:
                    github_aggregated[key]["times_used"] += 1
                    # Handle None values safely for time comparisons
                    if event_time:
                        existing_first = github_aggregated[key][
                            "first_seen_in_time_window"
                        ]
                        existing_last = github_aggregated[key]["last_used"]

                        if existing_first is None or event_time < existing_first:
                            github_aggregated[key][
                                "first_seen_in_time_window"
                            ] = event_time
                        if existing_last is None or event_time > existing_last:
                            github_aggregated[key]["last_used"] = event_time
                else:
                    github_aggregated[key] = {
                        "source_repo_fullname": github_repo,
                        "destination_principal_arn": destination_principal,
                        "times_used": 1,
                        "first_seen_in_time_window": event_time,
                        "last_used": event_time,
                    }
            else:
                # Skip non-GitHub events for now
                continue
        else:
            continue
    # Return aggregated relationships directly
    return list(github_aggregated.values())


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
    (AWSUser|AWSRole|AWSPrincipal)-[:ASSUMED_ROLE {lastupdated, times_used, first_seen_in_time_window, last_used}]->(AWSRole)

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


@timeit
def load_saml_role_assumptions(
    neo4j_session: neo4j.Session,
    aggregated_role_assumptions: List[Dict[str, Any]],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load aggregated SAML role assumption relationships into Neo4j using MatchLink pattern.

    Creates direct ASSUMED_ROLE_WITH_SAML relationships with aggregated properties:
    (AWSRole)-[:ASSUMED_ROLE_WITH_SAML {lastupdated, times_used, first_seen_in_time_window, last_used}]->(AWSRole)

    Assumes that both source principals and destination roles already exist in the graph.

    :type neo4j_session: neo4j.Session
    :param neo4j_session: The Neo4j session to use for database operations
    :type aggregated_role_assumptions: List[Dict[str, Any]]
    :param aggregated_role_assumptions: List of aggregated SAML role assumption relationships from transform function
    :type current_aws_account_id: str
    :param current_aws_account_id: The AWS account ID being synced
    :type aws_update_tag: int
    :param aws_update_tag: Timestamp tag for tracking data freshness
    :rtype: None
    """
    # Use MatchLink to create relationships between existing nodes
    matchlink_schema = AssumedRoleWithSAMLMatchLink()

    load_matchlinks(
        neo4j_session,
        matchlink_schema,
        aggregated_role_assumptions,
        lastupdated=aws_update_tag,
        _sub_resource_label="AWSAccount",
        _sub_resource_id=current_aws_account_id,
    )

    logger.info(
        f"Successfully loaded {len(aggregated_role_assumptions)} SAML role assumption relationships"
    )


@timeit
def load_web_identity_role_assumptions(
    neo4j_session: neo4j.Session,
    aggregated_role_assumptions: List[Dict[str, Any]],
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load aggregated WebIdentity role assumption relationships into Neo4j using MatchLink pattern.

    Creates direct ASSUMED_ROLE_WITH_WEB_IDENTITY relationships with aggregated properties:
    (GitHubRepository)-[:ASSUMED_ROLE_WITH_WEB_IDENTITY {lastupdated, times_used, first_seen_in_time_window, last_used}]->(AWSRole)

    Assumes that both source principals and destination roles already exist in the graph.

    :type neo4j_session: neo4j.Session
    :param neo4j_session: The Neo4j session to use for database operations
    :type aggregated_role_assumptions: List[Dict[str, Any]]
    :param aggregated_role_assumptions: List of aggregated WebIdentity role assumption relationships from transform function
    :type current_aws_account_id: str
    :param current_aws_account_id: The AWS account ID being synced
    :type aws_update_tag: int
    :param aws_update_tag: Timestamp tag for tracking data freshness
    :rtype: None
    """
    # Use MatchLink to create relationships between existing nodes
    matchlink_schema = GitHubRepoAssumeRoleWithWebIdentityMatchLink()

    load_matchlinks(
        neo4j_session,
        matchlink_schema,
        aggregated_role_assumptions,
        lastupdated=aws_update_tag,
        _sub_resource_label="AWSAccount",
        _sub_resource_id=current_aws_account_id,
    )

    logger.info(
        f"Successfully loaded {len(aggregated_role_assumptions)} WebIdentity role assumption relationships"
    )


def _convert_assumed_role_arn_to_role_arn(assumed_role_arn: str) -> str:
    """
    Convert an assumed role ARN to the original role ARN.

    Example:
    Input:  "arn:aws:sts::123456789012:assumed-role/MyRole/session-name"
    Output: "arn:aws:iam::123456789012:role/MyRole"
    """

    # Split the ARN into parts
    arn_parts = assumed_role_arn.split(":")
    if len(arn_parts) >= 6 and arn_parts[2] == "sts" and "assumed-role" in arn_parts[5]:
        # Extract account ID and role name
        account_id = arn_parts[4]
        resource_part = arn_parts[5]  # "assumed-role/MyRole/session-name"
        role_name = resource_part.split("/")[1]  # Extract "MyRole"

        # Construct the IAM role ARN
        return f"arn:aws:iam::{account_id}:role/{role_name}"

    # Return original ARN if conversion fails
    return assumed_role_arn


def _extract_github_repo_from_username(user_name: str) -> str:
    """
    Extract GitHub repository fullname from CloudTrail userName field.

    GitHub Actions CloudTrail events have userName in the format:
    "repo:{organization}/{repository}:{context}"
    """
    if not user_name:
        return ""

    parts = user_name.split(":")

    # Need at least 3 parts: ["repo", "{organization}/{repository}", "{context}"]
    if len(parts) < 3 or parts[0] != "repo":
        return ""

    # Extract "{organization}/{repository}"
    repo_fullname = parts[1]

    # Validate it looks like "{organization}/{repository}" format
    if repo_fullname.count("/") != 1:
        return ""

    # Ensure both organization and repo exist
    owner, repo = repo_fullname.split("/")
    if not owner or not repo:
        return ""

    return repo_fullname


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
    logger.info("Running CloudTrail management events cleanup job.")

    matchlink_schema = AssumedRoleMatchLink()
    cleanup_job = GraphJob.from_matchlink(
        matchlink_schema,
        "AWSAccount",
        current_aws_account_id,
        update_tag,
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync_assume_role_events(
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
    (AWSUser|AWSRole|AWSPrincipal)-[:ASSUMED_ROLE {times_used, first_seen_in_time_window, last_used, lastupdated}]->(AWSRole)

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
        f"Syncing {len(regions)} regions with {lookback_hours} hour lookback period"
    )

    total_role_assumptions = 0

    # Process events region by region
    for region in regions:
        logger.info(f"Processing CloudTrail events for region {region}")

        # Process AssumeRole events specifically
        logger.info(f"Fetching AssumeRole events specifically for region {region}")
        assume_role_events = get_assume_role_events(
            boto3_session=boto3_session,
            region=region,
            lookback_hours=lookback_hours,
        )

        # Transform AssumeRole events to role assumptions
        assume_role_assumptions = transform_assume_role_events_to_role_assumptions(
            events=assume_role_events,
        )

        # Load AssumeRole assumptions for this region
        load_role_assumptions(
            neo4j_session=neo4j_session,
            aggregated_role_assumptions=assume_role_assumptions,
            current_aws_account_id=current_aws_account_id,
            aws_update_tag=update_tag,
        )
        total_role_assumptions += len(assume_role_assumptions)
        logger.info(
            f"Loaded {len(assume_role_assumptions)} AssumeRole assumptions for region {region}"
        )

    # Run cleanup for stale relationships after processing all regions
    cleanup(neo4j_session, current_aws_account_id, update_tag)

    logger.info(
        f"CloudTrail management events sync completed successfully. "
        f"Processed {total_role_assumptions} total role assumption events across {len(regions)} regions."
    )


@timeit
def sync_saml_role_events(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync CloudTrail SAML management events to create ASSUMED_ROLE_WITH_SAML relationships.

    This function orchestrates the complete process:
    1. Fetch CloudTrail SAML management events region by region
    2. Transform events into role assumption records per region
    3. Load role assumption relationships into Neo4j for each region

    The resulting graph contains direct relationships like:
    (AWSRole)-[:ASSUMED_ROLE_WITH_SAML {times_used, first_seen_in_time_window, last_used, lastupdated}]->(AWSRole)

    :type neo4j_session: neo4j.Session
    :param neo4j_session: The Neo4j session
    :type boto3_session: boto3.Session
    :param boto3_session: The boto3 session to use for API calls
    :type regions: List[str]
    :param regions: List of AWS regions to sync
    :type current_aws_account_id: str
    :param current_aws_account_id: The AWS account ID being synced
    :type update_tag: int
    :param update_tag: Timestamp tag for tracking data freshness
    :rtype: None
    """
    # Extract lookback hours from common_job_parameters (set by CLI parameter)
    lookback_hours = common_job_parameters.get(
        "aws_cloudtrail_management_events_lookback_hours"
    )

    if not lookback_hours:
        logger.info(
            "CloudTrail SAML management events sync skipped - no lookback period specified"
        )
        return

    logger.info(
        f"Syncing SAML events for {len(regions)} regions with {lookback_hours} hour lookback period"
    )

    total_saml_role_assumptions = 0

    # Process events region by region
    for region in regions:
        logger.info(f"Processing CloudTrail SAML events for region {region}")

        # Process AssumeRoleWithSAML events specifically
        logger.info(
            f"Fetching AssumeRoleWithSAML events specifically for region {region}"
        )
        saml_role_events = get_saml_role_events(
            boto3_session=boto3_session,
            region=region,
            lookback_hours=lookback_hours,
        )

        # Transform AssumeRoleWithSAML events to role assumptions
        saml_role_assumptions = transform_saml_role_events_to_role_assumptions(
            events=saml_role_events,
        )

        # Load SAML role assumptions for this region
        load_saml_role_assumptions(
            neo4j_session=neo4j_session,
            aggregated_role_assumptions=saml_role_assumptions,
            current_aws_account_id=current_aws_account_id,
            aws_update_tag=update_tag,
        )
        total_saml_role_assumptions += len(saml_role_assumptions)
        logger.info(
            f"Loaded {len(saml_role_assumptions)} SAML role assumptions for region {region}"
        )

    logger.info(
        f"CloudTrail SAML management events sync completed successfully. "
        f"Processed {total_saml_role_assumptions} total SAML role assumption events across {len(regions)} regions."
    )


@timeit
def sync_web_identity_role_events(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync CloudTrail WebIdentity management events to create ASSUMED_ROLE_WITH_WEB_IDENTITY relationships.

    This function orchestrates the complete process:
    1. Fetch CloudTrail WebIdentity management events region by region
    2. Transform events into role assumption records per region
    3. Load role assumption relationships into Neo4j for each region

    The resulting graph contains direct relationships like:
    (GitHubRepository)-[:ASSUMED_ROLE_WITH_WEB_IDENTITY {times_used, first_seen_in_time_window, last_used, lastupdated}]->(AWSRole)

    :type neo4j_session: neo4j.Session
    :param neo4j_session: The Neo4j session
    :type boto3_session: boto3.Session
    :param boto3_session: The boto3 session to use for API calls
    :type regions: List[str]
    :param regions: List of AWS regions to sync
    :type current_aws_account_id: str
    :param current_aws_account_id: The AWS account ID being synced
    :type update_tag: int
    :param update_tag: Timestamp tag for tracking data freshness
    :rtype: None
    """
    # Extract lookback hours from common_job_parameters (set by CLI parameter)
    lookback_hours = common_job_parameters.get(
        "aws_cloudtrail_management_events_lookback_hours"
    )

    if not lookback_hours:
        logger.info(
            "CloudTrail WebIdentity management events sync skipped - no lookback period specified"
        )
        return

    logger.info(
        f"Syncing WebIdentity events for {len(regions)} regions with {lookback_hours} hour lookback period"
    )

    total_web_identity_role_assumptions = 0

    # Process events region by region
    for region in regions:
        logger.info(f"Processing CloudTrail WebIdentity events for region {region}")

        # Process AssumeRoleWithWebIdentity events specifically
        logger.info(
            f"Fetching AssumeRoleWithWebIdentity events specifically for region {region}"
        )
        web_identity_role_events = get_web_identity_role_events(
            boto3_session=boto3_session,
            region=region,
            lookback_hours=lookback_hours,
        )

        # Transform AssumeRoleWithWebIdentity events to role assumptions
        web_identity_role_assumptions = (
            transform_web_identity_role_events_to_role_assumptions(
                events=web_identity_role_events,
            )
        )

        # Load WebIdentity role assumptions for this region
        load_web_identity_role_assumptions(
            neo4j_session=neo4j_session,
            aggregated_role_assumptions=web_identity_role_assumptions,
            current_aws_account_id=current_aws_account_id,
            aws_update_tag=update_tag,
        )
        total_web_identity_role_assumptions += len(web_identity_role_assumptions)
        logger.info(
            f"Loaded {len(web_identity_role_assumptions)} WebIdentity role assumptions for region {region}"
        )

    logger.info(
        f"CloudTrail WebIdentity management events sync completed successfully. "
        f"Processed {total_web_identity_role_assumptions} total WebIdentity role assumption events across {len(regions)} regions."
    )


# Main sync function for when we decide to add more event types
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
    Main sync function for CloudTrail management events.

    Syncs AssumeRole, AssumeRoleWithSAML, and AssumeRoleWithWebIdentity events to create separate
    relationship types in the graph for security analysis.
    """
    # Sync regular AssumeRole events
    sync_assume_role_events(
        neo4j_session=neo4j_session,
        boto3_session=boto3_session,
        regions=regions,
        current_aws_account_id=current_aws_account_id,
        update_tag=update_tag,
        common_job_parameters=common_job_parameters,
    )

    # Sync SAML AssumeRoleWithSAML events
    sync_saml_role_events(
        neo4j_session=neo4j_session,
        boto3_session=boto3_session,
        regions=regions,
        current_aws_account_id=current_aws_account_id,
        update_tag=update_tag,
        common_job_parameters=common_job_parameters,
    )

    # Sync WebIdentity AssumeRoleWithWebIdentity events
    sync_web_identity_role_events(
        neo4j_session=neo4j_session,
        boto3_session=boto3_session,
        regions=regions,
        current_aws_account_id=current_aws_account_id,
        update_tag=update_tag,
        common_job_parameters=common_job_parameters,
    )
