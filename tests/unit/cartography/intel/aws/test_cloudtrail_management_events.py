from cartography.intel.aws.cloudtrail_management_events import (
    transform_assume_role_events_to_role_assumptions,
)
from cartography.intel.aws.cloudtrail_management_events import (
    transform_saml_role_events_to_role_assumptions,
)
from cartography.intel.aws.cloudtrail_management_events import (
    transform_web_identity_role_events_to_role_assumptions,
)
from tests.data.aws.cloudtrail_management_events import (
    ACCESS_DENIED_ASSUME_ROLE_CLOUDTRAIL_EVENTS,
)
from tests.data.aws.cloudtrail_management_events import (
    ACCESS_DENIED_SAML_ASSUME_ROLE_CLOUDTRAIL_EVENTS,
)
from tests.data.aws.cloudtrail_management_events import (
    ACCESS_DENIED_WEB_IDENTITY_ASSUME_ROLE_CLOUDTRAIL_EVENTS,
)

# Sample test data for AssumeRole events
SAMPLE_ASSUME_ROLE_EVENT = {
    "EventName": "AssumeRole",
    "EventTime": "2024-01-15T10:30:15.123000",
    "EventId": "test-event-id-123",
    "UserIdentity": {"arn": "arn:aws:iam::123456789012:user/john.doe"},
    "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::123456789012:user/john.doe"}, "requestParameters": {"roleArn": "arn:aws:iam::987654321098:role/ApplicationRole"}}',
}

# Sample test data for AssumeRoleWithSAML events
SAMPLE_ASSUME_ROLE_WITH_SAML_EVENT = {
    "EventName": "AssumeRoleWithSAML",
    "EventTime": "2024-01-15T11:45:22.456000",
    "EventId": "test-event-id-456",
    "UserIdentity": {
        "type": "SAMLUser",
        "principalId": "SAML:admin@example.com",
        "userName": "admin@example.com",
    },
    "CloudTrailEvent": '{"userIdentity": {"type": "SAMLUser", "principalId": "SAML:admin@example.com", "userName": "admin@example.com"}, "requestParameters": {"roleArn": "arn:aws:iam::987654321098:role/SAMLApplicationRole", "principalArn": "arn:aws:iam::123456789012:saml-provider/ExampleProvider"}, "responseElements": {"assumedRoleUser": {"arn": "arn:aws:sts::123456789012:assumed-role/SAMLRole/admin@example.com"}}}',
}

# Sample test data for AssumeRoleWithWebIdentity events (GitHub Actions)
SAMPLE_GITHUB_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT = {
    "EventName": "AssumeRoleWithWebIdentity",
    "EventTime": "2024-01-15T12:15:30.789000",
    "EventId": "test-event-id-789",
    "UserIdentity": {
        "type": "WebIdentityUser",
        "principalId": "repo:sublimagesec/sublimage:ref:refs/heads/main",
        "userName": "repo:sublimagesec/sublimage:ref:refs/heads/main",
        "identityProvider": "token.actions.githubusercontent.com",
    },
    "CloudTrailEvent": '{"userIdentity": {"type": "WebIdentityUser", "principalId": "repo:sublimagesec/sublimage:ref:refs/heads/main", "userName": "repo:sublimagesec/sublimage:ref:refs/heads/main", "identityProvider": "token.actions.githubusercontent.com"}, "requestParameters": {"roleArn": "arn:aws:iam::987654321098:role/GitHubActionsRole", "roleSessionName": "GitHubActions"}}',
}


def test_transform_single_assume_role_event():
    """Test that a single AssumeRole event is correctly transformed."""
    # Arrange
    events = [SAMPLE_ASSUME_ROLE_EVENT]

    # Act
    result = transform_assume_role_events_to_role_assumptions(events=events)

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


def test_transform_single_saml_role_event():
    """Test that a single AssumeRoleWithSAML event is correctly transformed."""
    # Arrange
    events = [SAMPLE_ASSUME_ROLE_WITH_SAML_EVENT]

    # Act
    result = transform_saml_role_events_to_role_assumptions(events=events)

    # Assert
    assert len(result) == 1

    assumption = result[0]
    assert assumption["source_principal_arn"] == "admin@example.com"
    assert (
        assumption["destination_principal_arn"]
        == "arn:aws:iam::987654321098:role/SAMLApplicationRole"
    )
    assert assumption["times_used"] == 1
    assert assumption["first_seen_in_time_window"] == "2024-01-15T11:45:22.456000"
    assert assumption["last_used"] == "2024-01-15T11:45:22.456000"


def test_transform_single_github_web_identity_role_event():
    """Test that a single GitHub AssumeRoleWithWebIdentity event is correctly transformed."""
    # Arrange
    events = [SAMPLE_GITHUB_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT]

    # Act
    result = transform_web_identity_role_events_to_role_assumptions(events=events)

    # Assert
    assert len(result) == 1

    assumption = result[0]
    assert assumption["source_repo_fullname"] == "sublimagesec/sublimage"
    assert (
        assumption["destination_principal_arn"]
        == "arn:aws:iam::987654321098:role/GitHubActionsRole"
    )
    assert assumption["times_used"] == 1
    assert assumption["first_seen_in_time_window"] == "2024-01-15T12:15:30.789000"
    assert assumption["last_used"] == "2024-01-15T12:15:30.789000"


def test_transform_assume_role_events_with_null_request_parameters():
    """Test that AssumeRole events with null requestParameters are gracefully skipped."""
    # Arrange
    events = ACCESS_DENIED_ASSUME_ROLE_CLOUDTRAIL_EVENTS

    # Act - This should no longer crash and should skip events with null requestParameters
    result = transform_assume_role_events_to_role_assumptions(events=events)

    # Assert - Events with null requestParameters should be skipped, resulting in empty list
    assert len(result) == 0


def test_transform_saml_role_events_with_null_request_parameters():
    """Test that AssumeRoleWithSAML events with null requestParameters are gracefully skipped."""
    # Arrange
    events = ACCESS_DENIED_SAML_ASSUME_ROLE_CLOUDTRAIL_EVENTS

    # Act - This should no longer crash and should skip events with null requestParameters
    result = transform_saml_role_events_to_role_assumptions(events=events)

    # Assert - Events with null requestParameters should be skipped, resulting in empty list
    assert len(result) == 0


def test_transform_web_identity_role_events_with_null_request_parameters():
    """Test that AssumeRoleWithWebIdentity events with null requestParameters are gracefully skipped."""
    # Arrange
    events = ACCESS_DENIED_WEB_IDENTITY_ASSUME_ROLE_CLOUDTRAIL_EVENTS

    # Act - This should no longer crash and should skip events with null requestParameters
    result = transform_web_identity_role_events_to_role_assumptions(events=events)

    # Assert - Events with null requestParameters should be skipped, resulting in empty list
    assert len(result) == 0
