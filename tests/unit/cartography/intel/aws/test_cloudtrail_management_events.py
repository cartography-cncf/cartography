from cartography.intel.aws.cloudtrail_management_events import (
    transform_cloudtrail_events_to_role_assumptions,
)
from tests.data.aws.cloudtrail_management_events import UNIT_TEST_ASSUME_ROLE_EVENT
from tests.data.aws.cloudtrail_management_events import (
    UNIT_TEST_EXPECTED_AGGREGATED_RESULT,
)
from tests.data.aws.cloudtrail_management_events import (
    UNIT_TEST_EXPECTED_DIFFERENT_PAIRS,
)
from tests.data.aws.cloudtrail_management_events import UNIT_TEST_MULTIPLE_STS_EVENTS


def test_transforms_assume_role_events_to_standardized_format():
    """
    Tests Raw CloudTrail AssumeRole events are converted to aggregated
    role assumption records with all required fields.
    """
    # Arrange: CloudTrail event from lookup_events API
    cloudtrail_events = [UNIT_TEST_ASSUME_ROLE_EVENT]

    # Act: Transform CloudTrail events to aggregated role assumptions
    aggregated_assumptions = transform_cloudtrail_events_to_role_assumptions(
        events=cloudtrail_events,
        region="us-east-1",
        current_aws_account_id="123456789012",
    )

    # Assert: Properly structured aggregated role assumption record created
    assert len(aggregated_assumptions) == 1
    assumption = aggregated_assumptions[0]

    assert (
        assumption["source_principal_arn"] == "arn:aws:iam::123456789012:user/john.doe"
    )
    assert (
        assumption["destination_principal_arn"]
        == "arn:aws:iam::987654321098:role/ApplicationRole"
    )
    assert assumption["times_used"] == 1
    assert assumption["first_seen_in_time_window"] == "2024-01-15T10:30:15.123000"
    assert assumption["last_used"] == "2024-01-15T10:30:15.123000"


def test_handles_different_sts_event_types():
    """
    Test that all STS role assumption event types (AssumeRole, AssumeRoleWithSAML,
    AssumeRoleWithWebIdentity) are properly transformed and aggregated.
    """
    # Arrange: Different types of STS events
    cloudtrail_events = UNIT_TEST_MULTIPLE_STS_EVENTS

    # Act: Transform all event types to aggregated role assumptions
    aggregated_assumptions = transform_cloudtrail_events_to_role_assumptions(
        events=cloudtrail_events,
        region="us-east-1",
        current_aws_account_id="123456789012",
    )

    # Assert: All event types properly transformed and aggregated
    assert len(aggregated_assumptions) == 3

    # Check that all expected destination roles are present
    destinations = [
        assumption["destination_principal_arn"] for assumption in aggregated_assumptions
    ]
    assert "arn:aws:iam::123456789012:role/AppRole" in destinations
    assert "arn:aws:iam::123456789012:role/SAMLRole" in destinations
    assert "arn:aws:iam::123456789012:role/WebRole" in destinations

    # Check that all records have aggregation properties
    for assumption in aggregated_assumptions:
        assert assumption["times_used"] == 1  # Each is a single event
        assert "first_seen_in_time_window" in assumption
        assert "last_used" in assumption


def test_aggregates_multiple_events_for_same_principal_role_pair():
    """
    Test that multiple role assumption events for the same (source, destination)
    pair are aggregated into a single record with usage analytics.
    """
    # Arrange: Create CloudTrail events that will produce the same aggregation
    # We'll create 3 events for the same user/role pair at different times
    cloudtrail_events = [
        {
            "EventName": "AssumeRole",
            "EventTime": "2024-01-15T09:00:00.000000",
            "UserIdentity": {"arn": "arn:aws:iam::123456789012:user/alice"},
            "Resources": [
                {
                    "ResourceType": "AWS::IAM::Role",
                    "ResourceName": "arn:aws:iam::123456789012:role/AppRole",
                    "AccountId": "123456789012",
                }
            ],
            "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::123456789012:user/alice"}, "requestParameters": {"roleArn": "arn:aws:iam::123456789012:role/AppRole"}}',
        },
        {
            "EventName": "AssumeRole",
            "EventTime": "2024-01-15T14:00:00.000000",
            "UserIdentity": {"arn": "arn:aws:iam::123456789012:user/alice"},
            "Resources": [
                {
                    "ResourceType": "AWS::IAM::Role",
                    "ResourceName": "arn:aws:iam::123456789012:role/AppRole",
                    "AccountId": "123456789012",
                }
            ],
            "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::123456789012:user/alice"}, "requestParameters": {"roleArn": "arn:aws:iam::123456789012:role/AppRole"}}',
        },
        {
            "EventName": "AssumeRole",
            "EventTime": "2024-01-15T17:00:00.000000",
            "UserIdentity": {"arn": "arn:aws:iam::123456789012:user/alice"},
            "Resources": [
                {
                    "ResourceType": "AWS::IAM::Role",
                    "ResourceName": "arn:aws:iam::123456789012:role/AppRole",
                    "AccountId": "123456789012",
                }
            ],
            "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::123456789012:user/alice"}, "requestParameters": {"roleArn": "arn:aws:iam::123456789012:role/AppRole"}}',
        },
    ]

    # Act: Transform CloudTrail events (with inline aggregation)
    aggregated = transform_cloudtrail_events_to_role_assumptions(
        events=cloudtrail_events,
        region="us-east-1",
        current_aws_account_id="123456789012",
    )

    # Assert: Single aggregated record with usage analytics
    assert len(aggregated) == 1

    agg_record = aggregated[0]
    expected = UNIT_TEST_EXPECTED_AGGREGATED_RESULT
    assert agg_record["source_principal_arn"] == expected["source_principal_arn"]
    assert (
        agg_record["destination_principal_arn"] == expected["destination_principal_arn"]
    )
    assert agg_record["times_used"] == expected["times_used"]
    assert (
        agg_record["first_seen_in_time_window"] == expected["first_seen_in_time_window"]
    )
    assert agg_record["last_used"] == expected["last_used"]


def test_preserves_separate_records_for_different_principal_role_pairs():
    """
    Test that different (source, destination) pairs maintain separate aggregated records.
    """
    # Arrange: Create CloudTrail events for different principal/role combinations
    cloudtrail_events = [
        {
            "EventName": "AssumeRole",
            "EventTime": "2024-01-15T10:00:00.000000",
            "UserIdentity": {"arn": "arn:aws:iam::123456789012:user/alice"},
            "Resources": [
                {
                    "ResourceType": "AWS::IAM::Role",
                    "ResourceName": "arn:aws:iam::123456789012:role/AppRole",
                    "AccountId": "123456789012",
                }
            ],
            "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::123456789012:user/alice"}, "requestParameters": {"roleArn": "arn:aws:iam::123456789012:role/AppRole"}}',
        },
        {
            "EventName": "AssumeRole",
            "EventTime": "2024-01-15T11:00:00.000000",
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
        {
            "EventName": "AssumeRole",
            "EventTime": "2024-01-15T12:00:00.000000",
            "UserIdentity": {"arn": "arn:aws:iam::123456789012:user/bob"},
            "Resources": [
                {
                    "ResourceType": "AWS::IAM::Role",
                    "ResourceName": "arn:aws:iam::123456789012:role/AppRole",
                    "AccountId": "123456789012",
                }
            ],
            "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::123456789012:user/bob"}, "requestParameters": {"roleArn": "arn:aws:iam::123456789012:role/AppRole"}}',
        },
    ]

    # Act: Transform CloudTrail events (with inline aggregation)
    aggregated = transform_cloudtrail_events_to_role_assumptions(
        events=cloudtrail_events,
        region="us-east-1",
        current_aws_account_id="123456789012",
    )

    # Assert: Three separate aggregated records maintained
    assert len(aggregated) == 3

    # Each should have times_used = 1 since they're all different pairs
    assert all(record["times_used"] == 1 for record in aggregated)

    # Verify we have the expected unique combinations
    pairs = {
        (record["source_principal_arn"], record["destination_principal_arn"])
        for record in aggregated
    }
    assert pairs == UNIT_TEST_EXPECTED_DIFFERENT_PAIRS
