from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.cloudtrail_management_events
import cartography.intel.aws.iam
from cartography.intel.aws.cloudtrail_management_events import sync
from tests.data.aws.cloudtrail_management_events import (
    INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID,
)
from tests.data.aws.cloudtrail_management_events import (
    INTEGRATION_TEST_AGGREGATION_IAM_ROLES,
)
from tests.data.aws.cloudtrail_management_events import (
    INTEGRATION_TEST_AGGREGATION_IAM_USERS,
)
from tests.data.aws.cloudtrail_management_events import (
    INTEGRATION_TEST_BASIC_ACCOUNT_ID,
)
from tests.data.aws.cloudtrail_management_events import INTEGRATION_TEST_BASIC_IAM_ROLES
from tests.data.aws.cloudtrail_management_events import INTEGRATION_TEST_BASIC_IAM_USERS
from tests.data.aws.cloudtrail_management_events import (
    INTEGRATION_TEST_CROSS_ACCOUNT_IAM_ROLES,
)
from tests.data.aws.cloudtrail_management_events import (
    INTEGRATION_TEST_CROSS_ACCOUNT_IAM_USERS,
)
from tests.data.aws.cloudtrail_management_events import (
    INTEGRATION_TEST_CROSS_ACCOUNT_ID,
)
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def _cleanup_neo4j(neo4j_session):
    """
    Clean up Neo4j database before each test.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n;")


def _ensure_local_neo4j_has_basic_test_data(neo4j_session):
    """Set up test IAM users and roles for basic relationships test."""
    # Load test users using cartography's IAM loader
    cartography.intel.aws.iam.load_users(
        neo4j_session,
        INTEGRATION_TEST_BASIC_IAM_USERS,
        INTEGRATION_TEST_BASIC_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Load test roles using cartography's IAM loader
    cartography.intel.aws.iam.load_roles(
        neo4j_session,
        INTEGRATION_TEST_BASIC_IAM_ROLES,
        INTEGRATION_TEST_BASIC_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Create cross-account role manually since it's in a different account
    neo4j_session.run(
        """
        MERGE (role:AWSRole:AWSPrincipal {arn: $role_arn})
        SET role.roleid = $role_id,
            role.name = $role_name,
            role.lastupdated = $update_tag
        """,
        role_arn="arn:aws:iam::987654321098:role/CrossAccountRole",
        role_id="AROA00000000CROSSACCOUNT",
        role_name="CrossAccountRole",
        update_tag=TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_aggregation_test_data(neo4j_session):
    """Set up test IAM users and roles for aggregation test."""
    cartography.intel.aws.iam.load_users(
        neo4j_session,
        INTEGRATION_TEST_AGGREGATION_IAM_USERS,
        INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    cartography.intel.aws.iam.load_roles(
        neo4j_session,
        INTEGRATION_TEST_AGGREGATION_IAM_ROLES,
        INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_cross_account_test_data(neo4j_session):
    """Set up test IAM users and roles for cross-account test."""
    cartography.intel.aws.iam.load_users(
        neo4j_session,
        INTEGRATION_TEST_CROSS_ACCOUNT_IAM_USERS,
        INTEGRATION_TEST_CROSS_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    cartography.intel.aws.iam.load_roles(
        neo4j_session,
        INTEGRATION_TEST_CROSS_ACCOUNT_IAM_ROLES,
        INTEGRATION_TEST_CROSS_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Create external role manually since it's in a different account
    neo4j_session.run(
        """
        MERGE (role:AWSRole:AWSPrincipal {arn: $role_arn})
        SET role.roleid = $role_id,
            role.name = $role_name,
            role.lastupdated = $update_tag
        """,
        role_arn="arn:aws:iam::333333333333:role/ExternalRole",
        role_id="AROA00000000EXTERNAL",
        role_name="ExternalRole",
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_assume_role_events",
    return_value=[
        {
            "EventName": "AssumeRole",
            "EventTime": "2024-01-15T10:30:15.123000",
            "UserIdentity": {"arn": "arn:aws:iam::123456789012:user/john.doe"},
            "Resources": [
                {
                    "ResourceType": "AWS::IAM::Role",
                    "ResourceName": "arn:aws:iam::123456789012:role/ApplicationRole",
                    "AccountId": "123456789012",
                }
            ],
            "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::123456789012:user/john.doe"}, "requestParameters": {"roleArn": "arn:aws:iam::123456789012:role/ApplicationRole"}}',
        },
        {
            "EventName": "AssumeRole",
            "EventTime": "2024-01-15T11:15:30.456000",
            "UserIdentity": {"arn": "arn:aws:iam::123456789012:user/alice"},
            "Resources": [
                {
                    "ResourceType": "AWS::IAM::Role",
                    "ResourceName": "arn:aws:iam::987654321098:role/CrossAccountRole",
                    "AccountId": "987654321098",
                }
            ],
            "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::123456789012:user/alice"}, "requestParameters": {"roleArn": "arn:aws:iam::987654321098:role/CrossAccountRole"}}',
        },
    ],
)
def test_cloudtrail_management_events_creates_assumed_role_relationships(
    mock_get_events, neo4j_session
):
    """
    OUTCOME: CloudTrail management events sync creates ASSUMED_ROLE relationships
    between existing principals and roles with correct properties.

    This is the primary happy path test - CloudTrail events should result in
    graph relationships that show actual role usage patterns.
    """
    # Arrange: Clean database and set up AWS account with IAM users and roles
    _cleanup_neo4j(neo4j_session)
    create_test_account(
        neo4j_session, INTEGRATION_TEST_BASIC_ACCOUNT_ID, TEST_UPDATE_TAG
    )
    _ensure_local_neo4j_has_basic_test_data(neo4j_session)

    # Act: Run CloudTrail sync with lookback period
    sync(
        neo4j_session,
        MagicMock(),  # boto3_session
        [TEST_REGION],
        INTEGRATION_TEST_BASIC_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"aws_cloudtrail_management_events_lookback_hours": 24},
    )

    # Assert: ASSUMED_ROLE relationships created between principals and roles
    assert check_rels(
        neo4j_session,
        "AWSPrincipal",
        "arn",
        "AWSRole",
        "arn",
        "ASSUMED_ROLE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:iam::123456789012:user/john.doe",
            "arn:aws:iam::123456789012:role/ApplicationRole",
        ),
        (
            "arn:aws:iam::123456789012:user/alice",
            "arn:aws:iam::987654321098:role/CrossAccountRole",
        ),
    }

    # Assert: Verify that all role assumptions have usage count of 1
    role_usage_results = neo4j_session.run(
        """
        MATCH (p:AWSPrincipal)-[r:ASSUMED_ROLE]->(role:AWSRole)
        WHERE p.arn STARTS WITH 'arn:aws:iam::123456789012:'
        RETURN r.times_used as times_used, r.last_used as last_used
        """
    ).data()

    assert len(role_usage_results) == 2
    for usage in role_usage_results:
        assert usage["times_used"] == 1
        assert usage["last_used"] is not None


@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_assume_role_events",
    return_value=[
        {
            "EventName": "AssumeRole",
            "EventTime": "2024-01-15T09:00:00.000000",
            "UserIdentity": {"arn": "arn:aws:iam::111111111111:user/test-user"},
            "Resources": [
                {
                    "ResourceType": "AWS::IAM::Role",
                    "ResourceName": "arn:aws:iam::111111111111:role/TestRole",
                    "AccountId": "111111111111",
                }
            ],
            "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::111111111111:user/test-user"}, "requestParameters": {"roleArn": "arn:aws:iam::111111111111:role/TestRole"}}',
        },
        {
            "EventName": "AssumeRole",
            "EventTime": "2024-01-15T14:00:00.000000",
            "UserIdentity": {"arn": "arn:aws:iam::111111111111:user/test-user"},
            "Resources": [
                {
                    "ResourceType": "AWS::IAM::Role",
                    "ResourceName": "arn:aws:iam::111111111111:role/TestRole",
                    "AccountId": "111111111111",
                }
            ],
            "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::111111111111:user/test-user"}, "requestParameters": {"roleArn": "arn:aws:iam::111111111111:role/TestRole"}}',
        },
        {
            "EventName": "AssumeRole",
            "EventTime": "2024-01-15T17:00:00.000000",
            "UserIdentity": {"arn": "arn:aws:iam::111111111111:user/test-user"},
            "Resources": [
                {
                    "ResourceType": "AWS::IAM::Role",
                    "ResourceName": "arn:aws:iam::111111111111:role/TestRole",
                    "AccountId": "111111111111",
                }
            ],
            "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::111111111111:user/test-user"}, "requestParameters": {"roleArn": "arn:aws:iam::111111111111:role/TestRole"}}',
        },
    ],
)
def test_cloudtrail_management_events_aggregates_multiple_role_assumptions(
    mock_get_events, neo4j_session
):
    """
    OUTCOME: Multiple CloudTrail events for the same principal/role pair
    are aggregated into a single ASSUMED_ROLE relationship with usage analytics.

    This tests the core aggregation behavior - multiple role assumptions
    should be consolidated with proper times_used, first_seen, last_seen tracking.
    """
    # Arrange: Clean database and set up AWS account with IAM data
    _cleanup_neo4j(neo4j_session)
    create_test_account(
        neo4j_session, INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID, TEST_UPDATE_TAG
    )
    _ensure_local_neo4j_has_aggregation_test_data(neo4j_session)

    # Act: Run CloudTrail sync
    sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"aws_cloudtrail_management_events_lookback_hours": 24},
    )

    # Assert: Single aggregated relationship created (not 3 separate ones)
    assert check_rels(
        neo4j_session,
        "AWSPrincipal",
        "arn",
        "AWSRole",
        "arn",
        "ASSUMED_ROLE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:iam::111111111111:user/test-user",
            "arn:aws:iam::111111111111:role/TestRole",
        ),
    }

    # Assert: Aggregated properties reflect multiple uses
    aggregated_usage = neo4j_session.run(
        """
        MATCH (p:AWSPrincipal {arn: 'arn:aws:iam::111111111111:user/test-user'})
              -[r:ASSUMED_ROLE]->
              (role:AWSRole {arn: 'arn:aws:iam::111111111111:role/TestRole'})
        RETURN r.times_used as times_used, r.first_seen_in_time_window as first_seen_in_time_window,
               r.last_used as last_used
        """
    ).single()

    assert aggregated_usage["times_used"] == 3
    assert aggregated_usage["first_seen_in_time_window"] == "2024-01-15T09:00:00.000000"
    assert aggregated_usage["last_used"] == "2024-01-15T17:00:00.000000"


@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_assume_role_events",
    return_value=[
        {
            "EventName": "AssumeRole",
            "EventTime": "2024-01-15T10:30:15.123000",
            "UserIdentity": {"arn": "arn:aws:iam::222222222222:user/cross-user"},
            "Resources": [
                {
                    "ResourceType": "AWS::IAM::Role",
                    "ResourceName": "arn:aws:iam::333333333333:role/ExternalRole",
                    "AccountId": "333333333333",
                }
            ],
            "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::222222222222:user/cross-user"}, "requestParameters": {"roleArn": "arn:aws:iam::333333333333:role/ExternalRole"}}',
        },
    ],
)
def test_cloudtrail_management_events_handles_cross_account_relationships(
    mock_get_events, neo4j_session
):
    """
    OUTCOME: CloudTrail events create ASSUMED_ROLE relationships even when
    the source and destination are in different AWS accounts.

    This tests cross-account role assumption tracking - a key security
    use case for understanding cross-account access patterns.
    """
    # Arrange: Clean database and set up AWS account with IAM data including cross-account role
    _cleanup_neo4j(neo4j_session)
    create_test_account(
        neo4j_session, INTEGRATION_TEST_CROSS_ACCOUNT_ID, TEST_UPDATE_TAG
    )
    _ensure_local_neo4j_has_cross_account_test_data(neo4j_session)

    # Act: Run CloudTrail sync
    sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        INTEGRATION_TEST_CROSS_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"aws_cloudtrail_management_events_lookback_hours": 24},
    )

    # Assert: Cross-account ASSUMED_ROLE relationship created
    assert check_rels(
        neo4j_session,
        "AWSPrincipal",
        "arn",
        "AWSRole",
        "arn",
        "ASSUMED_ROLE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:iam::222222222222:user/cross-user",
            "arn:aws:iam::333333333333:role/ExternalRole",
        ),
    }

    # Assert: Both source (current account) and destination (external account) nodes exist
    source_users = check_nodes(neo4j_session, "AWSUser", ["arn"])
    destination_roles = check_nodes(neo4j_session, "AWSRole", ["arn"])

    assert source_users is not None
    assert destination_roles is not None
    assert ("arn:aws:iam::222222222222:user/cross-user",) in source_users
    assert ("arn:aws:iam::333333333333:role/ExternalRole",) in destination_roles
