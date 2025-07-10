import json
from datetime import datetime

# Realistic STS AssumeRole event
STS_ASSUME_ROLE_EVENT = {
    "EventId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "EventName": "AssumeRole",
    "EventTime": datetime(2024, 1, 15, 10, 30, 15, 123000),
    "EventSource": "sts.amazonaws.com",
    "UserName": "arn:aws:iam::123456789012:user/john.doe",
    "UserIdentity": {
        "type": "IAMUser",
        "principalId": "AIDACKCEVSQ6C2EXAMPLE",
        "arn": "arn:aws:iam::123456789012:user/john.doe",
        "accountId": "123456789012",
        "userName": "john.doe",
    },
    "AwsRegion": "us-east-1",
    "SourceIPAddress": "192.168.1.100",
    "UserAgent": "aws-cli/2.0.0 Python/3.8.0 Linux/5.4.0-26-generic botocore/2.0.0dev0",
    "Resources": [
        {
            "ResourceType": "AWS::IAM::Role",
            "ResourceName": "arn:aws:iam::987654321098:role/CrossAccountRole",
            "AccountId": "987654321098",
        }
    ],
    "CloudTrailEvent": json.dumps(
        {
            "eventVersion": "1.05",
            "userIdentity": {
                "type": "IAMUser",
                "principalId": "AIDACKCEVSQ6C2EXAMPLE",
                "arn": "arn:aws:iam::123456789012:user/john.doe",
                "accountId": "123456789012",
                "userName": "john.doe",
            },
            "eventTime": "2024-01-15T10:30:15Z",
            "eventSource": "sts.amazonaws.com",
            "eventName": "AssumeRole",
            "awsRegion": "us-east-1",
            "sourceIPAddress": "192.168.1.100",
            "userAgent": "aws-cli/2.0.0 Python/3.8.0 Linux/5.4.0-26-generic botocore/2.0.0dev0",
            "requestParameters": {
                "roleArn": "arn:aws:iam::987654321098:role/CrossAccountRole",
                "roleSessionName": "john-doe-session-1642251015",
            },
            "responseElements": {
                "credentials": {
                    "sessionToken": "REDACTED",
                    "accessKeyId": "ASIACKCEVSQ6C2EXAMPLE",
                    "expiration": "Jan 15, 2024 11:30:15 AM",
                },
                "assumedRoleUser": {
                    "assumedRoleId": "AROACKCEVSQ6C2EXAMPLE:john-doe-session-1642251015",
                    "arn": "arn:aws:sts::987654321098:assumed-role/CrossAccountRole/john-doe-session-1642251015",
                },
            },
            "requestID": "c2d4638c-24b8-11e7-b13c-298444c2bb30",
            "eventID": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "eventType": "AwsApiCall",
            "recipientAccountId": "987654321098",
            "serviceEventDetails": {
                "responseElements": {"credentials": {"sessionToken": "REDACTED"}}
            },
        }
    ),
}

# STS AssumeRoleWithSAML event
STS_ASSUME_ROLE_WITH_SAML_EVENT = {
    "EventId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "EventName": "AssumeRoleWithSAML",
    "EventTime": datetime(2024, 1, 15, 11, 15, 30, 456000),
    "EventSource": "sts.amazonaws.com",
    "UserName": "SAML:jane.smith@company.com",
    "UserIdentity": {
        "type": "SAMLUser",
        "principalId": "SAML:jane.smith@company.com",
        "arn": "arn:aws:sts::123456789012:assumed-role/SAMLRole/jane.smith@company.com",
        "accountId": "123456789012",
    },
    "AwsRegion": "us-east-1",
    "SourceIPAddress": "10.0.1.50",
    "UserAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Resources": [
        {
            "ResourceType": "AWS::IAM::Role",
            "ResourceName": "arn:aws:iam::123456789012:role/SAMLRole",
            "AccountId": "123456789012",
        }
    ],
    "CloudTrailEvent": json.dumps(
        {
            "eventVersion": "1.05",
            "userIdentity": {
                "type": "SAMLUser",
                "principalId": "SAML:jane.smith@company.com",
                "arn": "arn:aws:sts::123456789012:assumed-role/SAMLRole/jane.smith@company.com",
                "accountId": "123456789012",
            },
            "eventTime": "2024-01-15T11:15:30Z",
            "eventSource": "sts.amazonaws.com",
            "eventName": "AssumeRoleWithSAML",
            "awsRegion": "us-east-1",
            "sourceIPAddress": "10.0.1.50",
            "requestParameters": {
                "roleArn": "arn:aws:iam::123456789012:role/SAMLRole",
                "principalArn": "arn:aws:iam::123456789012:saml-provider/CompanySAML",
            },
            "responseElements": {
                "assumedRoleUser": {
                    "assumedRoleId": "AROACKCEVSQ6C2EXAMPLE:jane.smith@company.com",
                    "arn": "arn:aws:sts::123456789012:assumed-role/SAMLRole/jane.smith@company.com",
                }
            },
        }
    ),
}

# STS AssumeRoleWithWebIdentity event
STS_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT = {
    "EventId": "9876543210abcdef-1234-5678-90ab-cdef12345678",
    "EventName": "AssumeRoleWithWebIdentity",
    "EventTime": datetime(2024, 1, 15, 12, 45, 0, 789000),
    "EventSource": "sts.amazonaws.com",
    "UserName": "arn:aws:sts::123456789012:assumed-role/WebIdentityRole/web-session-1642254300",
    "UserIdentity": {
        "type": "WebIdentityUser",
        "principalId": "arn:aws:sts::123456789012:assumed-role/WebIdentityRole/web-session-1642254300",
        "arn": "arn:aws:sts::123456789012:assumed-role/WebIdentityRole/web-session-1642254300",
        "accountId": "123456789012",
    },
    "AwsRegion": "us-west-2",
    "SourceIPAddress": "203.0.113.1",
    "UserAgent": "Boto3/1.26.0 Python/3.9.0 Linux/5.15.0 Botocore/1.29.0",
    "Resources": [
        {
            "ResourceType": "AWS::IAM::Role",
            "ResourceName": "arn:aws:iam::123456789012:role/WebIdentityRole",
            "AccountId": "123456789012",
        }
    ],
    "CloudTrailEvent": json.dumps(
        {
            "eventVersion": "1.05",
            "userIdentity": {
                "type": "WebIdentityUser",
                "principalId": "arn:aws:sts::123456789012:assumed-role/WebIdentityRole/web-session-1642254300",
                "arn": "arn:aws:sts::123456789012:assumed-role/WebIdentityRole/web-session-1642254300",
                "accountId": "123456789012",
            },
            "eventTime": "2024-01-15T12:45:00Z",
            "eventSource": "sts.amazonaws.com",
            "eventName": "AssumeRoleWithWebIdentity",
            "awsRegion": "us-west-2",
            "sourceIPAddress": "203.0.113.1",
            "requestParameters": {
                "roleArn": "arn:aws:iam::123456789012:role/WebIdentityRole",
                "roleSessionName": "web-session-1642254300",
            },
        }
    ),
}

# First page of paginated response
LOOKUP_EVENTS_RESPONSE_PAGE1 = {
    "Events": [STS_ASSUME_ROLE_EVENT, STS_ASSUME_ROLE_WITH_SAML_EVENT],
    "NextToken": "eyJOZXh0VG9rZW4iOiBudWxsLCAiYm90b190cnVuY2F0ZV9hbW91bnQiOiAyfQ==",
}

# Second page of paginated response
LOOKUP_EVENTS_RESPONSE_PAGE2 = {
    "Events": [STS_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT]
    # No NextToken indicates this is the last page
}

# Empty response (no events found)
LOOKUP_EVENTS_EMPTY_RESPONSE: dict = {"Events": []}

# Single page response (all events fit in one page)
LOOKUP_EVENTS_SINGLE_PAGE_RESPONSE = {
    "Events": [
        STS_ASSUME_ROLE_EVENT,
        STS_ASSUME_ROLE_WITH_SAML_EVENT,
        STS_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT,
    ]
}

# Expected combined results from pagination
EXPECTED_PAGINATED_EVENTS = [
    STS_ASSUME_ROLE_EVENT,
    STS_ASSUME_ROLE_WITH_SAML_EVENT,
    STS_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT,
]

# CloudTrail API error responses
CLOUDTRAIL_ACCESS_DENIED_ERROR = {
    "Error": {
        "Code": "AccessDenied",
        "Message": "User is not authorized to perform: cloudtrail:LookupEvents",
    }
}

CLOUDTRAIL_INVALID_TIME_RANGE_ERROR = {
    "Error": {
        "Code": "InvalidTimeRangeException",
        "Message": "Start time must be before end time",
    }
}

# Expected transformation results
EXPECTED_ROLE_ASSUMPTION_FROM_STS_ASSUME_ROLE = {
    "SourcePrincipal": "arn:aws:iam::123456789012:user/john.doe",
    "DestinationPrincipal": "arn:aws:iam::987654321098:role/CrossAccountRole",
    "Action": "AssumeRole",
    "EventId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "EventTime": datetime(2024, 1, 15, 10, 30, 15, 123000),
    "SourceIPAddress": "192.168.1.100",
    "UserAgent": "aws-cli/2.0.0 Python/3.8.0 Linux/5.4.0-26-generic botocore/2.0.0dev0",
    "AwsRegion": "us-east-1",
    "AccountId": "123456789012",
    "AssumedRoleArn": "arn:aws:iam::987654321098:role/CrossAccountRole",
    "PrincipalArn": "arn:aws:iam::123456789012:user/john.doe",
    "SessionName": "john-doe-session-1642251015",
    "RequestId": "c2d4638c-24b8-11e7-b13c-298444c2bb30",
    "RecipientAccountId": "987654321098",
}

EXPECTED_ROLE_ASSUMPTION_FROM_SAML = {
    "SourcePrincipal": "arn:aws:sts::123456789012:assumed-role/SAMLRole/jane.smith@company.com",
    "DestinationPrincipal": "arn:aws:iam::123456789012:role/SAMLRole",
    "Action": "AssumeRoleWithSAML",
    "EventId": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
    "EventTime": datetime(2024, 1, 15, 11, 15, 30, 456000),
    "SourceIPAddress": "10.0.1.50",
    "UserAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "AwsRegion": "us-east-1",
    "AccountId": "123456789012",
    "AssumedRoleArn": "arn:aws:iam::123456789012:role/SAMLRole",
    "PrincipalArn": "arn:aws:sts::123456789012:assumed-role/SAMLRole/jane.smith@company.com",
    "SessionName": None,  # SAML events might not have session names
    "RequestId": None,  # Not present in this test event
    "RecipientAccountId": None,  # Not present in this test event
}

EXPECTED_ROLE_ASSUMPTION_FROM_WEB_IDENTITY = {
    "SourcePrincipal": "arn:aws:sts::123456789012:assumed-role/WebIdentityRole/web-session-1642254300",
    "DestinationPrincipal": "arn:aws:iam::123456789012:role/WebIdentityRole",
    "Action": "AssumeRoleWithWebIdentity",
    "EventId": "9876543210abcdef-1234-5678-90ab-cdef12345678",
    "EventTime": datetime(2024, 1, 15, 12, 45, 0, 789000),
    "SourceIPAddress": "203.0.113.1",
    "UserAgent": "Boto3/1.26.0 Python/3.9.0 Linux/5.15.0 Botocore/1.29.0",
    "AwsRegion": "us-west-2",
    "AccountId": "123456789012",
    "AssumedRoleArn": "arn:aws:iam::123456789012:role/WebIdentityRole",
    "PrincipalArn": "arn:aws:sts::123456789012:assumed-role/WebIdentityRole/web-session-1642254300",
    "SessionName": "web-session-1642254300",
    "RequestId": None,  # Not present in this test event
    "RecipientAccountId": None,  # Not present in this test event
}

# Expected combined transformation results
EXPECTED_TRANSFORMED_ROLE_ASSUMPTIONS = [
    EXPECTED_ROLE_ASSUMPTION_FROM_STS_ASSUME_ROLE,
    EXPECTED_ROLE_ASSUMPTION_FROM_SAML,
    EXPECTED_ROLE_ASSUMPTION_FROM_WEB_IDENTITY,
]

# Non-STS event that should be filtered out
NON_STS_EVENT = {
    "EventId": "non-sts-event-id",
    "EventName": "CreateUser",
    "EventTime": datetime(2024, 1, 15, 9, 0, 0),
    "EventSource": "iam.amazonaws.com",
    "UserName": "admin-user",
}

# Malformed event (missing required fields)
MALFORMED_EVENT = {
    "EventId": "malformed-event-id",
    # Missing EventName and other critical fields
    "EventSource": "sts.amazonaws.com",
}

# Test data for aggregation scenarios
MULTIPLE_ASSUME_ROLE_EVENTS_SAME_PAIR = [
    {
        "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
        "DestinationPrincipal": "arn:aws:iam::123456789012:role/DataScientist",
        "Action": "AssumeRole",
        "EventId": "alice-ds-event-1",
        "EventTime": datetime(2024, 1, 15, 9, 0, 0),
        "SourceIPAddress": "192.168.1.100",
        "UserAgent": "aws-cli/2.0.0",
        "AwsRegion": "us-east-1",
        "AccountId": "123456789012",
        "AssumedRoleArn": "arn:aws:iam::123456789012:role/DataScientist",
        "PrincipalArn": "arn:aws:iam::123456789012:user/alice",
    },
    {
        "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
        "DestinationPrincipal": "arn:aws:iam::123456789012:role/DataScientist",
        "Action": "AssumeRole",
        "EventId": "alice-ds-event-2",
        "EventTime": datetime(2024, 1, 15, 13, 30, 0),
        "SourceIPAddress": "192.168.1.100",
        "UserAgent": "aws-cli/2.0.0",
        "AwsRegion": "us-east-1",
        "AccountId": "123456789012",
        "AssumedRoleArn": "arn:aws:iam::123456789012:role/DataScientist",
        "PrincipalArn": "arn:aws:iam::123456789012:user/alice",
    },
    {
        "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
        "DestinationPrincipal": "arn:aws:iam::123456789012:role/DataScientist",
        "Action": "AssumeRole",
        "EventId": "alice-ds-event-3",
        "EventTime": datetime(2024, 1, 15, 17, 15, 0),
        "SourceIPAddress": "192.168.1.100",
        "UserAgent": "aws-cli/2.0.0",
        "AwsRegion": "us-east-1",
        "AccountId": "123456789012",
        "AssumedRoleArn": "arn:aws:iam::123456789012:role/DataScientist",
        "PrincipalArn": "arn:aws:iam::123456789012:user/alice",
    },
]

# Expected aggregation result for the above events
EXPECTED_AGGREGATED_ALICE_DATASCIENTIST = {
    "source_principal_arn": "arn:aws:iam::123456789012:user/alice",
    "destination_principal_arn": "arn:aws:iam::123456789012:role/DataScientist",
    "times_used": 3,
    "first_seen_in_time_window": datetime(2024, 1, 15, 9, 0, 0),
    "last_seen": datetime(2024, 1, 15, 17, 15, 0),
    "lastused": datetime(2024, 1, 15, 17, 15, 0),
}

# Test data for different source types (User, Role, Principal)
CROSS_ACCOUNT_ROLE_ASSUMPTION_EVENTS = [
    {
        "SourcePrincipal": "arn:aws:iam::123456789012:user/service-account",
        "DestinationPrincipal": "arn:aws:iam::987654321098:role/CrossAccountRole",
        "Action": "AssumeRole",
        "EventId": "cross-account-event-1",
        "EventTime": datetime(2024, 1, 15, 10, 0, 0),
        "SourceIPAddress": "10.0.1.100",
        "UserAgent": "boto3/1.26.0",
        "AwsRegion": "us-west-2",
        "AccountId": "123456789012",
        "AssumedRoleArn": "arn:aws:iam::987654321098:role/CrossAccountRole",
        "PrincipalArn": "arn:aws:iam::123456789012:user/service-account",
    },
    {
        "SourcePrincipal": "arn:aws:iam::123456789012:role/ApplicationRole",
        "DestinationPrincipal": "arn:aws:iam::123456789012:role/DataAccessRole",
        "Action": "AssumeRole",
        "EventId": "role-to-role-event-1",
        "EventTime": datetime(2024, 1, 15, 11, 0, 0),
        "SourceIPAddress": "172.16.1.50",
        "UserAgent": "aws-sdk-java/1.12.0",
        "AwsRegion": "us-east-1",
        "AccountId": "123456789012",
        "AssumedRoleArn": "arn:aws:iam::123456789012:role/DataAccessRole",
        "PrincipalArn": "arn:aws:iam::123456789012:role/ApplicationRole",
    },
    {
        "SourcePrincipal": "arn:aws:sts::123456789012:federated-user/external-user",
        "DestinationPrincipal": "arn:aws:iam::123456789012:role/FederatedRole",
        "Action": "AssumeRoleWithSAML",
        "EventId": "federated-event-1",
        "EventTime": datetime(2024, 1, 15, 12, 0, 0),
        "SourceIPAddress": "203.0.113.100",
        "UserAgent": "Mozilla/5.0",
        "AwsRegion": "eu-west-1",
        "AccountId": "123456789012",
        "AssumedRoleArn": "arn:aws:iam::123456789012:role/FederatedRole",
        "PrincipalArn": "arn:aws:sts::123456789012:federated-user/external-user",
    },
]

# Events with incomplete data for testing error handling
INCOMPLETE_ROLE_ASSUMPTION_EVENTS = [
    {
        "SourcePrincipal": "arn:aws:iam::123456789012:user/incomplete-user",
        # Missing DestinationPrincipal
        "Action": "AssumeRole",
        "EventId": "incomplete-event-1",
        "EventTime": datetime(2024, 1, 15, 10, 0, 0),
    },
    {
        # Missing SourcePrincipal
        "DestinationPrincipal": "arn:aws:iam::123456789012:role/IncompleteRole",
        "Action": "AssumeRole",
        "EventId": "incomplete-event-2",
        "EventTime": datetime(2024, 1, 15, 11, 0, 0),
    },
    {
        "SourcePrincipal": "arn:aws:iam::123456789012:user/no-time-user",
        "DestinationPrincipal": "arn:aws:iam::123456789012:role/NoTimeRole",
        "Action": "AssumeRole",
        "EventId": "incomplete-event-3",
        # Missing EventTime
    },
]

# Expected Cypher query patterns for testing
EXPECTED_CYPHER_QUERY_PATTERNS = {
    "unwind": "UNWIND $assumptions AS assumption",
    "arn_conversion": "Convert assumed role ARNs to IAM role ARNs for source matching",
    "union_call": "CALL {",
    "aws_user_match": "MATCH (source:AWSUser {arn: source_role_arn})",
    "aws_role_match": "MATCH (source:AWSRole {arn: source_role_arn})",
    "aws_principal_match": "MATCH (source:AWSPrincipal {arn: source_role_arn})",
    "destination_merge": "MERGE (dest:AWSRole {arn: assumption.destination_principal_arn})",
    "relationship_merge": "MERGE (source_node)-[rel:ASSUMED_ROLE]->(dest)",
    "times_used_aggregation": "rel.times_used = COALESCE(rel.times_used, 0) + assumption.times_used",
    "first_seen_in_time_window_aggregation": "CASE WHEN assumption.first_seen_in_time_window <",
    "last_seen_aggregation": "CASE WHEN assumption.last_seen >",
    "lastused_aggregation": "CASE WHEN assumption.last_seen >",
    "lastupdated_set": "rel.lastupdated = $aws_update_tag",
}

# =============================================================================
# UNIT TEST MOCK DATA
# =============================================================================
# Clean, focused mock data for unit tests that focus on core functionality
# rather than extensive edge cases.

# Simple CloudTrail event for basic transformation testing
UNIT_TEST_ASSUME_ROLE_EVENT = {
    "EventId": "test-event-123",
    "EventName": "AssumeRole",
    "EventTime": "2024-01-15T10:30:15.123000",
    "UserIdentity": {
        "type": "User",
        "arn": "arn:aws:iam::123456789012:user/john.doe",
    },
    "Resources": [
        {
            "ResourceType": "AWS::IAM::Role",
            "ResourceName": "arn:aws:iam::987654321098:role/ApplicationRole",
            "AccountId": "987654321098",
        }
    ],
    "CloudTrailEvent": json.dumps(
        {
            "requestParameters": {
                "roleArn": "arn:aws:iam::987654321098:role/ApplicationRole",
                "roleSessionName": "ApplicationSession",
            },
            "responseElements": {
                "assumedRoleUser": {
                    "arn": "arn:aws:sts::987654321098:assumed-role/ApplicationRole/ApplicationSession"
                }
            },
        }
    ),
}

# CloudTrail events for different STS event types
UNIT_TEST_MULTIPLE_STS_EVENTS = [
    {
        "EventName": "AssumeRole",
        "EventId": "assume-role-event",
        "EventTime": "2024-01-15T10:00:00.000000",
        "UserIdentity": {"arn": "arn:aws:iam::123456789012:user/alice"},
        "Resources": [
            {
                "ResourceType": "AWS::IAM::Role",
                "ResourceName": "arn:aws:iam::123456789012:role/AppRole",
                "AccountId": "123456789012",
            }
        ],
        "CloudTrailEvent": json.dumps(
            {"requestParameters": {"roleArn": "arn:aws:iam::123456789012:role/AppRole"}}
        ),
    },
    {
        "EventName": "AssumeRoleWithSAML",
        "EventId": "saml-event",
        "EventTime": "2024-01-15T11:00:00.000000",
        "UserIdentity": {"arn": "arn:aws:iam::123456789012:saml-user/saml-user"},
        "Resources": [
            {
                "ResourceType": "AWS::IAM::Role",
                "ResourceName": "arn:aws:iam::123456789012:role/SAMLRole",
                "AccountId": "123456789012",
            }
        ],
        "CloudTrailEvent": json.dumps(
            {
                "requestParameters": {
                    "roleArn": "arn:aws:iam::123456789012:role/SAMLRole"
                }
            }
        ),
    },
    {
        "EventName": "AssumeRoleWithWebIdentity",
        "EventId": "web-identity-event",
        "EventTime": "2024-01-15T12:00:00.000000",
        "UserIdentity": {"arn": "arn:aws:iam::123456789012:web-identity-user/web-user"},
        "Resources": [
            {
                "ResourceType": "AWS::IAM::Role",
                "ResourceName": "arn:aws:iam::123456789012:role/WebRole",
                "AccountId": "123456789012",
            }
        ],
        "CloudTrailEvent": json.dumps(
            {"requestParameters": {"roleArn": "arn:aws:iam::123456789012:role/WebRole"}}
        ),
    },
]

# Multiple events for the same principal/role pair (aggregation testing)
UNIT_TEST_AGGREGATION_EVENTS = [
    {
        "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
        "DestinationPrincipal": "arn:aws:iam::123456789012:role/AppRole",
        "EventTime": "2024-01-15T09:00:00.000000",
    },
    {
        "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
        "DestinationPrincipal": "arn:aws:iam::123456789012:role/AppRole",
        "EventTime": "2024-01-15T14:00:00.000000",
    },
    {
        "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
        "DestinationPrincipal": "arn:aws:iam::123456789012:role/AppRole",
        "EventTime": "2024-01-15T17:00:00.000000",
    },
]

# Expected aggregated result for the above events
UNIT_TEST_EXPECTED_AGGREGATED_RESULT = {
    "source_principal_arn": "arn:aws:iam::123456789012:user/alice",
    "destination_principal_arn": "arn:aws:iam::123456789012:role/AppRole",
    "times_used": 3,
    "first_seen_in_time_window": "2024-01-15T09:00:00.000000",
    "last_used": "2024-01-15T17:00:00.000000",
}

# Different principal/role pairs for testing separate aggregation
UNIT_TEST_DIFFERENT_PAIRS_EVENTS = [
    {
        "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
        "DestinationPrincipal": "arn:aws:iam::123456789012:role/AppRole",
        "EventTime": "2024-01-15T10:00:00.000000",
    },
    {
        "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
        "DestinationPrincipal": "arn:aws:iam::987654321098:role/CrossAccountRole",
        "EventTime": "2024-01-15T11:00:00.000000",
    },
    {
        "SourcePrincipal": "arn:aws:iam::123456789012:user/bob",
        "DestinationPrincipal": "arn:aws:iam::123456789012:role/AppRole",
        "EventTime": "2024-01-15T12:00:00.000000",
    },
]

# Expected pairs for different principal/role combinations
UNIT_TEST_EXPECTED_DIFFERENT_PAIRS = {
    ("arn:aws:iam::123456789012:user/alice", "arn:aws:iam::123456789012:role/AppRole"),
    (
        "arn:aws:iam::123456789012:user/alice",
        "arn:aws:iam::987654321098:role/CrossAccountRole",
    ),
    ("arn:aws:iam::123456789012:user/bob", "arn:aws:iam::123456789012:role/AppRole"),
}

# Simple role assumption for MatchLink testing
UNIT_TEST_SIMPLE_ROLE_ASSUMPTION = {
    "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
    "DestinationPrincipal": "arn:aws:iam::123456789012:role/AppRole",
    "EventTime": "2024-01-15T10:00:00.000000",
}

# Mock data for sync orchestration testing
UNIT_TEST_MOCK_EVENTS = [{"EventName": "AssumeRole", "EventId": "test-event"}]
UNIT_TEST_MOCK_ASSUMPTIONS = [
    {"SourcePrincipal": "arn:aws:iam::123456789012:user/alice"}
]

# =============================================================================
# INTEGRATION TEST MOCK DATA
# =============================================================================
# Mock data for integration tests that work with real Neo4j database
# Each test uses different account IDs and ARNs to prevent data isolation issues

# Test data for basic relationships test
INTEGRATION_TEST_BASIC_ACCOUNT_ID = "123456789012"
INTEGRATION_TEST_BASIC_IAM_USERS = [
    {
        "UserName": "john.doe",
        "UserId": "AIDACKCEVSQ6C2EXAMPLE",
        "Arn": "arn:aws:iam::123456789012:user/john.doe",
        "Path": "/",
        "CreateDate": datetime(2024, 1, 1, 10, 0, 0),
    },
    {
        "UserName": "alice",
        "UserId": "AIDACKCEVSQ6C2ALICE",
        "Arn": "arn:aws:iam::123456789012:user/alice",
        "Path": "/",
        "CreateDate": datetime(2024, 1, 1, 10, 0, 0),
    },
]

INTEGRATION_TEST_BASIC_IAM_ROLES = [
    {
        "RoleName": "ApplicationRole",
        "RoleId": "AROA00000000000000001",
        "Arn": "arn:aws:iam::123456789012:role/ApplicationRole",
        "Path": "/",
        "CreateDate": datetime(2024, 1, 1, 10, 0, 0),
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::123456789012:root"},
                    "Action": "sts:AssumeRole",
                }
            ],
        },
    },
]

INTEGRATION_TEST_BASIC_ROLE_ASSUMPTIONS = [
    {
        "source_principal_arn": "arn:aws:iam::123456789012:user/john.doe",
        "destination_principal_arn": "arn:aws:iam::123456789012:role/ApplicationRole",
        "times_used": 1,
        "first_seen_in_time_window": "2024-01-15T10:30:15.123000",
        "last_used": "2024-01-15T10:30:15.123000",
    },
    {
        "source_principal_arn": "arn:aws:iam::123456789012:user/alice",
        "destination_principal_arn": "arn:aws:iam::987654321098:role/CrossAccountRole",
        "times_used": 1,
        "first_seen_in_time_window": "2024-01-15T11:15:30.456000",
        "last_used": "2024-01-15T11:15:30.456000",
    },
]

# Test data for aggregation test - different account to prevent conflicts
INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID = "111111111111"
INTEGRATION_TEST_AGGREGATION_IAM_USERS = [
    {
        "UserName": "test-user",
        "UserId": "AIDACKCEVSQ6C2TESTUSER",
        "Arn": "arn:aws:iam::111111111111:user/test-user",
        "Path": "/",
        "CreateDate": datetime(2024, 1, 1, 10, 0, 0),
    },
]

INTEGRATION_TEST_AGGREGATION_IAM_ROLES = [
    {
        "RoleName": "TestRole",
        "RoleId": "AROA00000000000000002",
        "Arn": "arn:aws:iam::111111111111:role/TestRole",
        "Path": "/",
        "CreateDate": datetime(2024, 1, 1, 10, 0, 0),
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::111111111111:root"},
                    "Action": "sts:AssumeRole",
                }
            ],
        },
    },
]

INTEGRATION_TEST_AGGREGATION_ROLE_ASSUMPTIONS = [
    {
        "source_principal_arn": "arn:aws:iam::111111111111:user/test-user",
        "destination_principal_arn": "arn:aws:iam::111111111111:role/TestRole",
        "times_used": 3,
        "first_seen_in_time_window": "2024-01-15T09:00:00.000000",
        "last_used": "2024-01-15T17:00:00.000000",
    },
]

# Test data for cross-account test - different account to prevent conflicts
INTEGRATION_TEST_CROSS_ACCOUNT_ID = "222222222222"
INTEGRATION_TEST_CROSS_ACCOUNT_IAM_USERS = [
    {
        "UserName": "cross-user",
        "UserId": "AIDACKCEVSQ6C2CROSSUSER",
        "Arn": "arn:aws:iam::222222222222:user/cross-user",
        "Path": "/",
        "CreateDate": datetime(2024, 1, 1, 10, 0, 0),
    },
]

INTEGRATION_TEST_CROSS_ACCOUNT_IAM_ROLES = [
    {
        "RoleName": "ExternalRole",
        "RoleId": "AROA00000000000000003",
        "Arn": "arn:aws:iam::333333333333:role/ExternalRole",
        "Path": "/",
        "CreateDate": datetime(2024, 1, 1, 10, 0, 0),
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::222222222222:root"},
                    "Action": "sts:AssumeRole",
                }
            ],
        },
    },
]

INTEGRATION_TEST_CROSS_ACCOUNT_ROLE_ASSUMPTIONS = [
    {
        "source_principal_arn": "arn:aws:iam::222222222222:user/cross-user",
        "destination_principal_arn": "arn:aws:iam::333333333333:role/ExternalRole",
        "times_used": 1,
        "first_seen_in_time_window": "2024-01-15T10:30:15.123000",
        "last_used": "2024-01-15T10:30:15.123000",
    }
]

# Legacy data for backward compatibility - keeping these for any existing usage
INTEGRATION_TEST_IAM_USERS = INTEGRATION_TEST_BASIC_IAM_USERS
INTEGRATION_TEST_IAM_ROLES = INTEGRATION_TEST_BASIC_IAM_ROLES
