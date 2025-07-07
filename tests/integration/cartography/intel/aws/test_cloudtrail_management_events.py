import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.cloudtrail_management_events
import cartography.intel.aws.iam
from cartography.intel.aws.cloudtrail_management_events import sync
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "123456789012"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def _cleanup_neo4j(neo4j_session):
    """Clean up any existing data in Neo4j before running a test."""
    neo4j_session.run("MATCH (n) DETACH DELETE n;")


# Test IAM Users data
TEST_IAM_USERS = [
    {
        "UserName": "john.doe",
        "UserId": "AIDACKCEVSQ6C2EXAMPLE",
        "Arn": "arn:aws:iam::123456789012:user/john.doe",
        "Path": "/",
        "CreateDate": datetime.datetime(2024, 1, 1, 10, 0, 0),
    },
    {
        "UserName": "alice",
        "UserId": "AIDACKCEVSQ6C2ALICE",
        "Arn": "arn:aws:iam::123456789012:user/alice",
        "Path": "/",
        "CreateDate": datetime.datetime(2024, 1, 1, 10, 0, 0),
    },
]

# Test IAM Roles data
TEST_IAM_ROLES = [
    {
        "RoleName": "CrossAccountRole",
        "RoleId": "AROA00000000000000000",
        "Arn": "arn:aws:iam::987654321098:role/CrossAccountRole",
        "Path": "/",
        "CreateDate": datetime.datetime(2024, 1, 1, 10, 0, 0),
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
    {
        "RoleName": "SAMLRole",
        "RoleId": "AROA00000000000000001",
        "Arn": "arn:aws:iam::123456789012:role/SAMLRole",
        "Path": "/",
        "CreateDate": datetime.datetime(2024, 1, 1, 10, 0, 0),
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": "arn:aws:iam::123456789012:saml-provider/CompanySAML"
                    },
                    "Action": "sts:AssumeRoleWithSAML",
                }
            ],
        },
    },
    {
        "RoleName": "WebIdentityRole",
        "RoleId": "AROA00000000000000002",
        "Arn": "arn:aws:iam::123456789012:role/WebIdentityRole",
        "Path": "/",
        "CreateDate": datetime.datetime(2024, 1, 1, 10, 0, 0),
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": "arn:aws:iam::123456789012:oidc-provider/example.com"
                    },
                    "Action": "sts:AssumeRoleWithWebIdentity",
                }
            ],
        },
    },
]


def _ensure_local_neo4j_has_test_iam_data(neo4j_session):
    """
    Set up test IAM users and roles in Neo4j for the test.
    """
    # Load test users
    cartography.intel.aws.iam.load_users(
        neo4j_session,
        TEST_IAM_USERS,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Load test roles
    cartography.intel.aws.iam.load_roles(
        neo4j_session,
        TEST_IAM_ROLES,
        TEST_ACCOUNT_ID,
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


@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_cloudtrail_events",
    return_value=[],  # We'll override this in the test
)
@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "transform_cloudtrail_events_to_role_assumptions",
    return_value=[
        # User john.doe assumes cross-account role
        {
            "SourcePrincipal": "arn:aws:iam::123456789012:user/john.doe",
            "DestinationPrincipal": "arn:aws:iam::987654321098:role/CrossAccountRole",
            "Action": "AssumeRole",
            "EventId": "test-event-1",
            "EventTime": "2024-01-15T10:30:15.123000",
        },
        # User alice assumes SAMLRole
        {
            "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
            "DestinationPrincipal": "arn:aws:iam::123456789012:role/SAMLRole",
            "Action": "AssumeRole",
            "EventId": "test-event-2",
            "EventTime": "2024-01-15T11:15:30.456000",
        },
        # User alice also assumes WebIdentityRole
        {
            "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
            "DestinationPrincipal": "arn:aws:iam::123456789012:role/WebIdentityRole",
            "Action": "AssumeRole",
            "EventId": "test-event-3",
            "EventTime": "2024-01-15T12:45:00.789000",
        },
    ],
)
def test_sync_cloudtrail_management_events_creates_assumed_role_relationships(
    mock_transform, mock_get_events, neo4j_session
):
    """
    Test that the CloudTrail management events sync creates ASSUMED_ROLE relationships
    with correct aggregated properties.
    """
    # Arrange
    _cleanup_neo4j(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _ensure_local_neo4j_has_test_iam_data(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AWS_ID": TEST_ACCOUNT_ID,
        "aws_cloudtrail_management_events_lookback_hours": 24,
    }

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check that expected nodes exist
    assert check_nodes(neo4j_session, "AWSUser", ["arn", "name"]) == {
        ("arn:aws:iam::123456789012:user/john.doe", "john.doe"),
        ("arn:aws:iam::123456789012:user/alice", "alice"),
    }

    assert check_nodes(neo4j_session, "AWSRole", ["arn", "name"]) == {
        ("arn:aws:iam::987654321098:role/CrossAccountRole", "CrossAccountRole"),
        ("arn:aws:iam::123456789012:role/SAMLRole", "SAMLRole"),
        ("arn:aws:iam::123456789012:role/WebIdentityRole", "WebIdentityRole"),
    }

    # Assert - Check that ASSUMED_ROLE relationships exist with correct properties
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
            "arn:aws:iam::987654321098:role/CrossAccountRole",
        ),
        (
            "arn:aws:iam::123456789012:user/alice",
            "arn:aws:iam::123456789012:role/SAMLRole",
        ),
        (
            "arn:aws:iam::123456789012:user/alice",
            "arn:aws:iam::123456789012:role/WebIdentityRole",
        ),
    }

    # Assert - Check relationship properties using manual query (since check_rels doesn't return properties)
    assumed_role_rels = neo4j_session.run(
        """
        MATCH (source:AWSPrincipal)-[rel:ASSUMED_ROLE]->(dest:AWSRole)
        RETURN source.arn as source_arn, dest.arn as dest_arn,
               rel.times_used as times_used, rel.first_seen as first_seen,
               rel.last_seen as last_seen, rel.lastused as lastused
        ORDER BY source.arn, dest.arn
        """,
    ).data()

    expected_rels = [
        {
            "source_arn": "arn:aws:iam::123456789012:user/alice",
            "dest_arn": "arn:aws:iam::123456789012:role/SAMLRole",
            "times_used": 1,
            "first_seen": "2024-01-15T11:15:30.456000",
            "last_seen": "2024-01-15T11:15:30.456000",
            "lastused": "2024-01-15T11:15:30.456000",
        },
        {
            "source_arn": "arn:aws:iam::123456789012:user/alice",
            "dest_arn": "arn:aws:iam::123456789012:role/WebIdentityRole",
            "times_used": 1,
            "first_seen": "2024-01-15T12:45:00.789000",
            "last_seen": "2024-01-15T12:45:00.789000",
            "lastused": "2024-01-15T12:45:00.789000",
        },
        {
            "source_arn": "arn:aws:iam::123456789012:user/john.doe",
            "dest_arn": "arn:aws:iam::987654321098:role/CrossAccountRole",
            "times_used": 1,
            "first_seen": "2024-01-15T10:30:15.123000",
            "last_seen": "2024-01-15T10:30:15.123000",
            "lastused": "2024-01-15T10:30:15.123000",
        },
    ]

    assert assumed_role_rels == expected_rels


@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_cloudtrail_events",
    return_value=[],
)
@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "transform_cloudtrail_events_to_role_assumptions",
    return_value=[],
)
def test_sync_cloudtrail_management_events_with_no_events(
    mock_transform, mock_get_events, neo4j_session
):
    """
    Test that the sync function handles no events gracefully.
    """
    # Arrange
    _cleanup_neo4j(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _ensure_local_neo4j_has_test_iam_data(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AWS_ID": TEST_ACCOUNT_ID,
        "aws_cloudtrail_management_events_lookback_hours": 24,
    }

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - No ASSUMED_ROLE relationships should be created
    assert (
        check_rels(
            neo4j_session,
            "AWSPrincipal",
            "arn",
            "AWSRole",
            "arn",
            "ASSUMED_ROLE",
            rel_direction_right=True,
        )
        == set()
    )


def test_sync_cloudtrail_management_events_skipped_when_no_lookback_hours(
    neo4j_session,
):
    """
    Test that the sync function skips execution when no lookback hours are specified.
    """
    # Arrange
    _cleanup_neo4j(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _ensure_local_neo4j_has_test_iam_data(neo4j_session)

    # Don't include lookback hours in common_job_parameters
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AWS_ID": TEST_ACCOUNT_ID,
    }

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - No ASSUMED_ROLE relationships should be created
    assert (
        check_rels(
            neo4j_session,
            "AWSPrincipal",
            "arn",
            "AWSRole",
            "arn",
            "ASSUMED_ROLE",
            rel_direction_right=True,
        )
        == set()
    )


@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_cloudtrail_events",
    return_value=[],
)
@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "transform_cloudtrail_events_to_role_assumptions",
    side_effect=[
        # First region succeeds
        [
            {
                "SourcePrincipal": "arn:aws:iam::123456789012:user/john.doe",
                "DestinationPrincipal": "arn:aws:iam::987654321098:role/CrossAccountRole",
                "Action": "AssumeRole",
                "EventId": "test-event-1",
                "EventTime": "2024-01-15T10:30:15.123000",
            }
        ],
        # Second region fails
        Exception("Access denied"),
        # Third region succeeds
        [
            {
                "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
                "DestinationPrincipal": "arn:aws:iam::123456789012:role/SAMLRole",
                "Action": "AssumeRole",
                "EventId": "test-event-2",
                "EventTime": "2024-01-15T11:15:30.456000",
            }
        ],
    ],
)
def test_sync_cloudtrail_management_events_continues_on_region_failure(
    mock_transform, mock_get_events, neo4j_session
):
    """
    Test that the sync function continues processing other regions even when one fails.
    """
    # Arrange
    _cleanup_neo4j(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _ensure_local_neo4j_has_test_iam_data(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AWS_ID": TEST_ACCOUNT_ID,
        "aws_cloudtrail_management_events_lookback_hours": 24,
    }

    # Act - Process multiple regions where one fails
    sync(
        neo4j_session,
        boto3_session,
        ["us-east-1", "us-west-2", "eu-west-1"],  # Three regions
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Should have relationships from the successful regions only
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
            "arn:aws:iam::987654321098:role/CrossAccountRole",
        ),
        (
            "arn:aws:iam::123456789012:user/alice",
            "arn:aws:iam::123456789012:role/SAMLRole",
        ),
    }


@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "get_cloudtrail_events",
    return_value=[],
)
@patch.object(
    cartography.intel.aws.cloudtrail_management_events,
    "transform_cloudtrail_events_to_role_assumptions",
    return_value=[
        # Simulate multiple events for the same (source, destination) pair
        {
            "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
            "DestinationPrincipal": "arn:aws:iam::123456789012:role/SAMLRole",
            "EventTime": "2024-01-15T09:00:00.000000",
            "Action": "AssumeRole",
            "EventId": "event-1",
        },
        {
            "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
            "DestinationPrincipal": "arn:aws:iam::123456789012:role/SAMLRole",
            "EventTime": "2024-01-15T14:00:00.000000",
            "Action": "AssumeRole",
            "EventId": "event-2",
        },
        {
            "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
            "DestinationPrincipal": "arn:aws:iam::123456789012:role/SAMLRole",
            "EventTime": "2024-01-15T17:00:00.000000",
            "Action": "AssumeRole",
            "EventId": "event-3",
        },
    ],
)
def test_sync_cloudtrail_management_events_aggregates_multiple_events(
    mock_transform, mock_get_events, neo4j_session
):
    """
    Test that multiple events for the same source-destination pair are properly aggregated.
    """
    # Arrange
    _cleanup_neo4j(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _ensure_local_neo4j_has_test_iam_data(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AWS_ID": TEST_ACCOUNT_ID,
        "aws_cloudtrail_management_events_lookback_hours": 24,
    }

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Should have exactly one aggregated relationship
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
            "arn:aws:iam::123456789012:user/alice",
            "arn:aws:iam::123456789012:role/SAMLRole",
        ),
    }

    # Assert - Check aggregated properties
    aggregated_rel = neo4j_session.run(
        """
        MATCH (source:AWSPrincipal)-[rel:ASSUMED_ROLE]->(dest:AWSRole)
        WHERE source.arn = 'arn:aws:iam::123456789012:user/alice'
        AND dest.arn = 'arn:aws:iam::123456789012:role/SAMLRole'
        RETURN rel.times_used as times_used, rel.first_seen as first_seen,
               rel.last_seen as last_seen, rel.lastused as lastused
        """,
    ).single()

    assert aggregated_rel["times_used"] == 3
    assert aggregated_rel["first_seen"] == "2024-01-15T09:00:00.000000"
    assert aggregated_rel["last_seen"] == "2024-01-15T17:00:00.000000"
    assert aggregated_rel["lastused"] == "2024-01-15T17:00:00.000000"


def test_sync_cloudtrail_management_events_cross_account_relationships(neo4j_session):
    """
    Test that cross-account role assumptions are properly handled.
    """
    # Arrange
    _cleanup_neo4j(neo4j_session)
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _ensure_local_neo4j_has_test_iam_data(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AWS_ID": TEST_ACCOUNT_ID,
        "aws_cloudtrail_management_events_lookback_hours": 24,
    }

    # Mock CloudTrail events that include cross-account role assumptions
    with (
        patch.object(
            cartography.intel.aws.cloudtrail_management_events,
            "get_cloudtrail_events",
            return_value=[],
        ),
        patch.object(
            cartography.intel.aws.cloudtrail_management_events,
            "transform_cloudtrail_events_to_role_assumptions",
            return_value=[
                {
                    "SourcePrincipal": "arn:aws:iam::123456789012:user/john.doe",
                    "DestinationPrincipal": "arn:aws:iam::987654321098:role/CrossAccountRole",
                    "Action": "AssumeRole",
                    "EventId": "test-event-1",
                    "EventTime": "2024-01-15T10:30:15.123000",
                }
            ],
        ),
    ):
        # Act
        sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

    # Assert - Cross-account relationship should exist
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
            "arn:aws:iam::987654321098:role/CrossAccountRole",
        ),
    }

    # Assert - Both source and destination nodes should exist
    assert check_nodes(neo4j_session, "AWSUser", ["arn"]) == {
        ("arn:aws:iam::123456789012:user/john.doe",),
        ("arn:aws:iam::123456789012:user/alice",),
    }

    assert check_nodes(neo4j_session, "AWSRole", ["arn"]) == {
        ("arn:aws:iam::987654321098:role/CrossAccountRole",),
        ("arn:aws:iam::123456789012:role/SAMLRole",),
        ("arn:aws:iam::123456789012:role/WebIdentityRole",),
    }
