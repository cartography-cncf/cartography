import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import boto3
import neo4j

from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.util import aws_handle_regions, timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_cloudtrail_events(
    boto3_session: boto3.Session, 
    region: str,
    lookback_hours: int = 24
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
        "cloudtrail", 
        region_name=region, 
        config=get_botocore_config()
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
        paginator = client.get_paginator('lookup_events')
        
        page_iterator = paginator.paginate(
            LookupAttributes=[
                {
                    'AttributeKey': 'EventSource',
                    'AttributeValue': 'sts.amazonaws.com'
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            PaginationConfig={
                'MaxItems': 10000,  # Reasonable limit to prevent excessive API calls
                'PageSize': 50      # CloudTrail API limit per page
            }
        )
        
        for page in page_iterator:
            events.extend(page.get('Events', []))
            
        logger.info(f"Retrieved {len(events)} CloudTrail management events from region '{region}'")
        
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
    
    logger.info(f"Transforming {len(events)} CloudTrail events to role assumptions for region '{region}'")
    
    for event in events:
        try:
            assumption = _extract_role_assumption_from_event(event, region, current_aws_account_id)
            if assumption:
                role_assumptions.append(assumption)
        except Exception as e:
            logger.warning(
                f"Failed to transform CloudTrail event {event.get('EventId', 'unknown')}: {str(e)}"
            )
            continue
    
    logger.info(f"Successfully transformed {len(role_assumptions)} role assumptions from {len(events)} events")
    return role_assumptions


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
    event_name = event.get('EventName')
    
    # Only process STS role assumption events
    if event_name not in ['AssumeRole', 'AssumeRoleWithSAML', 'AssumeRoleWithWebIdentity']:
        return None
    
    # Extract source principal (who is assuming the role)
    source_principal = _extract_source_principal(event)
    if not source_principal:
        logger.debug(f"Could not extract source principal from event {event.get('EventId')}")
        return None
    
    # Extract destination principal (role being assumed)
    destination_principal = _extract_destination_principal(event)
    if not destination_principal:
        logger.debug(f"Could not extract destination principal from event {event.get('EventId')}")
        return None
    
    # Build the standardized role assumption record
    assumption = {
        'SourcePrincipal': source_principal,
        'DestinationPrincipal': destination_principal,
        'Action': event_name,
        'EventId': event.get('EventId'),
        'EventTime': event.get('EventTime'),
        'SourceIPAddress': event.get('SourceIPAddress'),
        'UserAgent': event.get('UserAgent'),
        'AwsRegion': event.get('AwsRegion', region),
        'AccountId': current_aws_account_id,
        'AssumedRoleArn': destination_principal,  # For relationship targeting
        'PrincipalArn': source_principal,        # For relationship targeting
    }
    
    # Add additional context from CloudTrail event JSON
    cloudtrail_event = _parse_cloudtrail_event_json(event.get('CloudTrailEvent'))
    if cloudtrail_event:
        assumption.update({
            'SessionName': _extract_session_name(cloudtrail_event, event_name),
            'RequestId': cloudtrail_event.get('requestID'),
            'RecipientAccountId': cloudtrail_event.get('recipientAccountId'),
        })
    
    return assumption


def _extract_source_principal(event: Dict[str, Any]) -> Optional[str]:
    """Extract the source principal (who is assuming the role) from a CloudTrail event."""
    user_identity = event.get('UserIdentity', {})
    
    # Try to get ARN from UserIdentity
    if user_identity.get('arn'):
        return user_identity['arn']
    
    # For SAML users, construct ARN from available info
    if user_identity.get('type') == 'SAMLUser':
        principal_id = user_identity.get('principalId')
        if principal_id:
            return principal_id
    
    # For Web Identity users, use the assumed role ARN if available
    if user_identity.get('type') == 'WebIdentityUser':
        return user_identity.get('arn')
    
    # Fallback to UserName if available
    user_name = event.get('UserName')
    if user_name:
        return user_name
    
    return None


def _extract_destination_principal(event: Dict[str, Any]) -> Optional[str]:
    """Extract the destination principal (role being assumed) from a CloudTrail event."""
    # Parse the CloudTrail event JSON for detailed information
    cloudtrail_event = _parse_cloudtrail_event_json(event.get('CloudTrailEvent'))
    if not cloudtrail_event:
        return None
    
    # Extract role ARN from request parameters
    request_params = cloudtrail_event.get('requestParameters', {})
    role_arn = request_params.get('roleArn')
    
    if role_arn:
        return role_arn
    
    # Fallback: try to extract from response elements for some STS calls
    response_elements = cloudtrail_event.get('responseElements', {})
    assumed_role_user = response_elements.get('assumedRoleUser', {})
    if assumed_role_user.get('arn'):
        # Convert assumed role ARN back to role ARN
        # e.g., "arn:aws:sts::123456789012:assumed-role/MyRole/session" -> "arn:aws:iam::123456789012:role/MyRole"
        assumed_role_arn = assumed_role_user['arn']
        return _convert_assumed_role_arn_to_role_arn(assumed_role_arn)
    
    return None


def _extract_session_name(cloudtrail_event: Dict[str, Any], event_name: str) -> Optional[str]:
    """Extract the role session name from CloudTrail event details."""
    request_params = cloudtrail_event.get('requestParameters', {})
    return request_params.get('roleSessionName')


def _parse_cloudtrail_event_json(cloudtrail_event_str: Optional[str]) -> Optional[Dict[str, Any]]:
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
        arn_parts = assumed_role_arn.split(':')
        if len(arn_parts) >= 6 and arn_parts[2] == 'sts' and 'assumed-role' in arn_parts[5]:
            # Extract account ID and role name
            account_id = arn_parts[4]
            resource_part = arn_parts[5]  # "assumed-role/MyRole/session-name"
            role_name = resource_part.split('/')[1]  # Extract "MyRole"
            
            # Construct the IAM role ARN
            return f"arn:aws:iam::{account_id}:role/{role_name}"
    except (IndexError, AttributeError):
        logger.debug(f"Could not convert assumed role ARN to role ARN: {assumed_role_arn}")
    
    # Return original ARN if conversion fails
    return assumed_role_arn