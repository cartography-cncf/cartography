from cartography.intel.aws.cloudtrail_management_events import (
    transform_assume_role_events_to_role_assumptions,
)

# Sample test data for AssumeRole events
SAMPLE_ASSUME_ROLE_EVENT = {
    "EventName": "AssumeRole",
    "EventTime": "2024-01-15T10:30:15.123000",
    "EventId": "test-event-id-123",
    "UserIdentity": {"arn": "arn:aws:iam::123456789012:user/john.doe"},
    "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::123456789012:user/john.doe"}, "requestParameters": {"roleArn": "arn:aws:iam::987654321098:role/ApplicationRole"}}',
}


def test_transform_single_assume_role_event():
    """Test that a single AssumeRole event is correctly transformed."""
    # Arrange
    events = [SAMPLE_ASSUME_ROLE_EVENT]

    # Act
    result = transform_assume_role_events_to_role_assumptions(
        events=events, region="us-east-1", current_aws_account_id="123456789012"
    )

    # Assert
    assert len(result) == 1

    assumption = result[0]
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
    assert assumption["event_types"] == ["AssumeRole"]
    assert assumption["assume_role_count"] == 1
    assert assumption["saml_count"] == 0
    assert assumption["web_identity_count"] == 0
