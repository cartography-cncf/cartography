from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from botocore.exceptions import ReadTimeoutError

import cartography.intel.aws.cloudtrail_management_events as cloudtrail_management_events
from cartography.intel.aws.cloudtrail import CloudTrailTransientRegionFailure
from cartography.intel.aws.cloudtrail_management_events import get_assume_role_events
from cartography.intel.aws.cloudtrail_management_events import get_saml_role_events
from cartography.intel.aws.cloudtrail_management_events import (
    get_web_identity_role_events,
)
from cartography.intel.aws.cloudtrail_management_events import sync_assume_role_events
from cartography.intel.aws.cloudtrail_management_events import (
    transform_assume_role_events_to_role_assumptions,
)
from cartography.intel.aws.cloudtrail_management_events import (
    transform_saml_role_events_to_role_assumptions,
)
from cartography.intel.aws.cloudtrail_management_events import (
    transform_web_identity_role_events_to_role_assumptions,
)
from cartography.intel.aws.util.botocore_config import get_botocore_config
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
        "principalId": "repo:example-org/example-repo:ref:refs/heads/main",
        "userName": "repo:example-org/example-repo:ref:refs/heads/main",
        "identityProvider": "token.actions.githubusercontent.com",
    },
    "CloudTrailEvent": '{"userIdentity": {"type": "WebIdentityUser", "principalId": "repo:example-org/example-repo:ref:refs/heads/main", "userName": "repo:example-org/example-repo:ref:refs/heads/main", "identityProvider": "token.actions.githubusercontent.com"}, "requestParameters": {"roleArn": "arn:aws:iam::987654321098:role/GitHubActionsRole", "roleSessionName": "GitHubActions"}}',
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


def test_transform_assume_role_event_keeps_govcloud_partition():
    """An assumed-role source ARN is normalized to its role ARN without leaving its partition."""
    # Arrange
    events = [
        {
            "EventName": "AssumeRole",
            "EventTime": "2024-01-15T10:30:15.123000",
            "EventId": "test-event-id-gov",
            "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws-us-gov:sts::111122223333:assumed-role/ExampleRole/example-session"}, "requestParameters": {"roleArn": "arn:aws-us-gov:iam::444455556666:role/ExampleTargetRole"}}',
        },
    ]

    # Act
    result = transform_assume_role_events_to_role_assumptions(events=events)

    # Assert
    assert [
        (r["source_principal_arn"], r["destination_principal_arn"]) for r in result
    ] == [
        (
            "arn:aws-us-gov:iam::111122223333:role/ExampleRole",
            "arn:aws-us-gov:iam::444455556666:role/ExampleTargetRole",
        ),
    ]


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
    assert assumption["source_repo_fullname"] == "example-org/example-repo"
    assert (
        assumption["destination_principal_arn"]
        == "arn:aws:iam::987654321098:role/GitHubActionsRole"
    )
    assert assumption["times_used"] == 1
    assert assumption["first_seen_in_time_window"] == "2024-01-15T12:15:30.789000"
    assert assumption["last_used"] == "2024-01-15T12:15:30.789000"


@pytest.mark.parametrize(
    "user_name, expected",
    [
        ("repo:octo-org/octo-repo:pull_request", "octo-org/octo-repo"),
        (
            "repo:octo-org@123456/octo-repo@456789:pull_request",
            "octo-org/octo-repo",
        ),
        (
            "repo:octo-org@123456/octo-repo@456789:ref:refs/heads/main",
            "octo-org/octo-repo",
        ),
        (
            "repo:octo-org@123456/octo-repo@456789:environment:production",
            "octo-org/octo-repo",
        ),
        ("repo:octo-org@abc/octo-repo@456789:pull_request", ""),
        ("repo:@123456/octo-repo@456789:pull_request", ""),
        ("repo:octo-org@123456/octo-repo@:pull_request", ""),
        ("repo:octo-org/team/octo-repo:pull_request", ""),
        ("repo:octo-org/octo-repo", ""),
        ("", ""),
    ],
)
def test_extract_github_repo_from_username(user_name, expected):
    """Legacy and immutable GitHub OIDC subjects resolve to the same repository fullname."""
    assert (
        cloudtrail_management_events._extract_github_repo_from_username(user_name)
        == expected
    )


def test_transform_github_web_identity_events_aggregate_legacy_and_immutable_subjects():
    """A repository that moves to immutable subjects keeps a single aggregated assumption."""
    # Arrange
    immutable_event = {
        "EventName": "AssumeRoleWithWebIdentity",
        "EventTime": "2026-07-20T09:00:00.000000",
        "EventId": "test-event-id-immutable",
        "CloudTrailEvent": '{"userIdentity": {"type": "WebIdentityUser", "principalId": "repo:example-org@123456/example-repo@456789:ref:refs/heads/main", "userName": "repo:example-org@123456/example-repo@456789:ref:refs/heads/main", "identityProvider": "token.actions.githubusercontent.com"}, "requestParameters": {"roleArn": "arn:aws:iam::987654321098:role/GitHubActionsRole", "roleSessionName": "GitHubActions"}}',
    }
    events = [SAMPLE_GITHUB_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT, immutable_event]

    # Act
    result = transform_web_identity_role_events_to_role_assumptions(events=events)

    # Assert
    assert result == [
        {
            "source_repo_fullname": "example-org/example-repo",
            "destination_principal_arn": "arn:aws:iam::987654321098:role/GitHubActionsRole",
            "times_used": 2,
            "first_seen_in_time_window": "2024-01-15T12:15:30.789000",
            "last_used": "2026-07-20T09:00:00.000000",
        },
    ]


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


@pytest.mark.parametrize(
    "getter",
    [
        get_assume_role_events,
        get_saml_role_events,
        get_web_identity_role_events,
    ],
)
def test_get_role_events_raise_transient_region_failure_on_503(getter):
    boto3_session = MagicMock()
    page_iterator = MagicMock()
    page_iterator.__iter__ = MagicMock(
        side_effect=ClientError(
            {
                "Error": {
                    "Code": "ServiceUnavailable",
                    "Message": "Service Unavailable",
                },
                "ResponseMetadata": {"HTTPStatusCode": 503},
            },
            "LookupEvents",
        )
    )
    boto3_session.client.return_value.get_paginator.return_value.paginate.return_value = (
        page_iterator
    )

    with pytest.raises(CloudTrailTransientRegionFailure):
        getter(boto3_session, "me-central-1", 24)

    assert boto3_session.client.call_args.kwargs["config"] == get_botocore_config()


@pytest.mark.parametrize(
    "getter",
    [
        get_assume_role_events,
        get_saml_role_events,
        get_web_identity_role_events,
    ],
)
def test_get_role_events_raise_transient_region_failure_on_read_timeout(getter):
    boto3_session = MagicMock()
    page_iterator = MagicMock()
    page_iterator.__iter__ = MagicMock(
        side_effect=ReadTimeoutError(
            endpoint_url="https://cloudtrail.me-central-1.amazonaws.com/",
            error="timeout",
        )
    )
    boto3_session.client.return_value.get_paginator.return_value.paginate.return_value = (
        page_iterator
    )

    with pytest.raises(CloudTrailTransientRegionFailure):
        getter(boto3_session, "me-central-1", 24)


def test_sync_assume_role_events_skips_cleanup_on_transient_region_failure(
    monkeypatch: pytest.MonkeyPatch,
):
    cleanup_calls = []
    load_calls = []

    def fake_get_assume_role_events(
        boto3_session: MagicMock, region: str, lookback_hours: int
    ):
        if region == "me-central-1":
            raise CloudTrailTransientRegionFailure("transient failure")
        return [{"EventId": f"{region}-event"}]

    def fake_transform_assume_role_events_to_role_assumptions(events):
        return [{"event_count": len(events)}]

    def fake_load_role_assumptions(**kwargs):
        load_calls.append(kwargs["aggregated_role_assumptions"])

    def fake_cleanup(*args, **kwargs):
        cleanup_calls.append((args, kwargs))

    monkeypatch.setattr(
        cloudtrail_management_events,
        "get_assume_role_events",
        fake_get_assume_role_events,
    )
    monkeypatch.setattr(
        cloudtrail_management_events,
        "transform_assume_role_events_to_role_assumptions",
        fake_transform_assume_role_events_to_role_assumptions,
    )
    monkeypatch.setattr(
        cloudtrail_management_events,
        "load_role_assumptions",
        fake_load_role_assumptions,
    )
    monkeypatch.setattr(cloudtrail_management_events, "cleanup", fake_cleanup)

    sync_assume_role_events(
        neo4j_session=MagicMock(),
        boto3_session=MagicMock(),
        regions=["us-east-1", "me-central-1"],
        current_aws_account_id="123456789012",
        update_tag=123,
        common_job_parameters={
            "aws_cloudtrail_management_events_lookback_hours": 24,
        },
    )

    assert len(load_calls) == 1
    assert cleanup_calls == []
