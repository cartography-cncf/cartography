from datetime import datetime
from datetime import timedelta
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

import boto3
from botocore.exceptions import ClientError

from cartography.intel.aws.cloudtrail_management_events import (
    _aggregate_role_assumptions,
)
from cartography.intel.aws.cloudtrail_management_events import get_cloudtrail_events
from cartography.intel.aws.cloudtrail_management_events import load_role_assumptions
from cartography.intel.aws.cloudtrail_management_events import sync
from cartography.intel.aws.cloudtrail_management_events import (
    transform_cloudtrail_events_to_role_assumptions,
)
from tests.data.aws.cloudtrail_management_events import (
    CROSS_ACCOUNT_ROLE_ASSUMPTION_EVENTS,
)
from tests.data.aws.cloudtrail_management_events import (
    EXPECTED_AGGREGATED_ALICE_DATASCIENTIST,
)
from tests.data.aws.cloudtrail_management_events import EXPECTED_CYPHER_QUERY_PATTERNS
from tests.data.aws.cloudtrail_management_events import EXPECTED_PAGINATED_EVENTS
from tests.data.aws.cloudtrail_management_events import (
    EXPECTED_ROLE_ASSUMPTION_FROM_SAML,
)
from tests.data.aws.cloudtrail_management_events import (
    EXPECTED_ROLE_ASSUMPTION_FROM_STS_ASSUME_ROLE,
)
from tests.data.aws.cloudtrail_management_events import (
    EXPECTED_ROLE_ASSUMPTION_FROM_WEB_IDENTITY,
)
from tests.data.aws.cloudtrail_management_events import (
    EXPECTED_TRANSFORMED_ROLE_ASSUMPTIONS,
)
from tests.data.aws.cloudtrail_management_events import (
    INCOMPLETE_ROLE_ASSUMPTION_EVENTS,
)
from tests.data.aws.cloudtrail_management_events import LOOKUP_EVENTS_EMPTY_RESPONSE
from tests.data.aws.cloudtrail_management_events import LOOKUP_EVENTS_RESPONSE_PAGE1
from tests.data.aws.cloudtrail_management_events import LOOKUP_EVENTS_RESPONSE_PAGE2
from tests.data.aws.cloudtrail_management_events import (
    LOOKUP_EVENTS_SINGLE_PAGE_RESPONSE,
)
from tests.data.aws.cloudtrail_management_events import MALFORMED_EVENT
from tests.data.aws.cloudtrail_management_events import (
    MULTIPLE_ASSUME_ROLE_EVENTS_SAME_PAIR,
)
from tests.data.aws.cloudtrail_management_events import NON_STS_EVENT
from tests.data.aws.cloudtrail_management_events import STS_ASSUME_ROLE_EVENT
from tests.data.aws.cloudtrail_management_events import STS_ASSUME_ROLE_WITH_SAML_EVENT
from tests.data.aws.cloudtrail_management_events import (
    STS_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT,
)


class TestGetCloudTrailEvents:
    """Test suite for get_cloudtrail_events function."""

    @patch("cartography.intel.aws.cloudtrail_management_events.get_botocore_config")
    def test_get_cloudtrail_events_success_single_page(self, mock_botocore_config):
        """Test successful retrieval of CloudTrail events in a single page."""
        # Arrange
        mock_session = MagicMock(spec=boto3.Session)
        mock_client = MagicMock()
        mock_paginator = MagicMock()

        mock_session.client.return_value = mock_client
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [LOOKUP_EVENTS_SINGLE_PAGE_RESPONSE]

        region = "us-east-1"
        lookback_hours = 24

        # Act
        result = get_cloudtrail_events(mock_session, region, lookback_hours)

        # Assert - Verify client creation
        mock_session.client.assert_called_once_with(
            "cloudtrail", region_name=region, config=mock_botocore_config.return_value
        )

        # Assert - Verify paginator creation
        mock_client.get_paginator.assert_called_once_with("lookup_events")

        # Assert - Verify API call parameters
        expected_end_time = datetime.utcnow()
        expected_start_time = expected_end_time - timedelta(hours=lookback_hours)

        mock_paginator.paginate.assert_called_once()
        call_args = mock_paginator.paginate.call_args

        assert call_args[1]["LookupAttributes"] == [
            {"AttributeKey": "EventSource", "AttributeValue": "sts.amazonaws.com"}
        ]
        assert call_args[1]["PaginationConfig"] == {"MaxItems": 10000, "PageSize": 50}

        # Verify time range (allow small tolerance for test execution time)
        start_time_diff = abs(
            (call_args[1]["StartTime"] - expected_start_time).total_seconds()
        )
        end_time_diff = abs(
            (call_args[1]["EndTime"] - expected_end_time).total_seconds()
        )
        assert start_time_diff < 5  # Allow 5 seconds tolerance
        assert end_time_diff < 5

        # Assert - Verify results
        assert len(result) == 3
        assert result[0]["EventName"] == "AssumeRole"
        assert result[1]["EventName"] == "AssumeRoleWithSAML"
        assert result[2]["EventName"] == "AssumeRoleWithWebIdentity"
        assert result == EXPECTED_PAGINATED_EVENTS

    @patch("cartography.intel.aws.cloudtrail_management_events.get_botocore_config")
    def test_get_cloudtrail_events_success_with_pagination(self, mock_botocore_config):
        """Test successful retrieval of CloudTrail events across multiple pages."""
        # Arrange
        mock_session = MagicMock(spec=boto3.Session)
        mock_client = MagicMock()
        mock_paginator = MagicMock()

        mock_session.client.return_value = mock_client
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            LOOKUP_EVENTS_RESPONSE_PAGE1,
            LOOKUP_EVENTS_RESPONSE_PAGE2,
        ]

        region = "us-west-2"
        lookback_hours = 72

        # Act
        result = get_cloudtrail_events(mock_session, region, lookback_hours)

        # Assert - Verify pagination handling
        assert len(result) == 3
        assert result[0] == STS_ASSUME_ROLE_EVENT
        assert result[1] == STS_ASSUME_ROLE_WITH_SAML_EVENT
        assert result[2] == STS_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT
        assert result == EXPECTED_PAGINATED_EVENTS

        # Verify the time range reflects the 72-hour lookback
        call_args = mock_paginator.paginate.call_args
        time_diff = call_args[1]["EndTime"] - call_args[1]["StartTime"]
        assert (
            abs(time_diff.total_seconds() - (72 * 3600)) < 60
        )  # Allow 1 minute tolerance

    @patch("cartography.intel.aws.cloudtrail_management_events.get_botocore_config")
    def test_get_cloudtrail_events_empty_response(self, mock_botocore_config):
        """Test handling of empty CloudTrail response."""
        # Arrange
        mock_session = MagicMock(spec=boto3.Session)
        mock_client = MagicMock()
        mock_paginator = MagicMock()

        mock_session.client.return_value = mock_client
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [LOOKUP_EVENTS_EMPTY_RESPONSE]

        # Act
        result = get_cloudtrail_events(mock_session, "eu-west-1", 12)

        # Assert
        assert result == []
        assert len(result) == 0

    @patch("cartography.intel.aws.cloudtrail_management_events.get_botocore_config")
    def test_get_cloudtrail_events_default_lookback_hours(self, mock_botocore_config):
        """Test that default lookback hours parameter works correctly."""
        # Arrange
        mock_session = MagicMock(spec=boto3.Session)
        mock_client = MagicMock()
        mock_paginator = MagicMock()

        mock_session.client.return_value = mock_client
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [LOOKUP_EVENTS_SINGLE_PAGE_RESPONSE]

        # Act - Don't specify lookback_hours, should use default of 24
        result = get_cloudtrail_events(mock_session, "us-east-1")

        # Assert - Verify default 24 hour time range
        call_args = mock_paginator.paginate.call_args
        time_diff = call_args[1]["EndTime"] - call_args[1]["StartTime"]
        assert (
            abs(time_diff.total_seconds() - (24 * 3600)) < 60
        )  # Allow 1 minute tolerance

        # Assert - Verify results are returned correctly
        assert result == EXPECTED_PAGINATED_EVENTS

    @patch("cartography.intel.aws.cloudtrail_management_events.get_botocore_config")
    def test_get_cloudtrail_events_api_error_access_denied(self, mock_botocore_config):
        """Test handling of CloudTrail API access denied error."""
        # Arrange
        mock_session = MagicMock(spec=boto3.Session)
        mock_client = MagicMock()
        mock_paginator = MagicMock()

        mock_session.client.return_value = mock_client
        mock_client.get_paginator.return_value = mock_paginator

        # Simulate AccessDenied error
        mock_paginator.paginate.side_effect = ClientError(
            error_response={
                "Error": {
                    "Code": "AccessDenied",
                    "Message": "User is not authorized to perform: cloudtrail:LookupEvents",
                }
            },
            operation_name="LookupEvents",
        )

        # Act
        result = get_cloudtrail_events(mock_session, "us-east-1", 24)

        # Assert - Should return empty list and log warning (not raise exception)
        assert result == []

    @patch("cartography.intel.aws.cloudtrail_management_events.get_botocore_config")
    def test_get_cloudtrail_events_api_error_invalid_time_range(
        self, mock_botocore_config
    ):
        """Test handling of CloudTrail API invalid time range error."""
        # Arrange
        mock_session = MagicMock(spec=boto3.Session)
        mock_client = MagicMock()
        mock_paginator = MagicMock()

        mock_session.client.return_value = mock_client
        mock_client.get_paginator.return_value = mock_paginator

        # Simulate InvalidTimeRangeException
        mock_paginator.paginate.side_effect = ClientError(
            error_response={
                "Error": {
                    "Code": "InvalidTimeRangeException",
                    "Message": "Start time must be before end time",
                }
            },
            operation_name="LookupEvents",
        )

        # Act
        result = get_cloudtrail_events(mock_session, "ap-southeast-1", 24)

        # Assert - Should return empty list and log warning (not raise exception)
        assert result == []

    @patch("cartography.intel.aws.cloudtrail_management_events.get_botocore_config")
    def test_get_cloudtrail_events_generic_exception(self, mock_botocore_config):
        """Test handling of generic exceptions."""
        # Arrange
        mock_session = MagicMock(spec=boto3.Session)
        mock_client = MagicMock()
        mock_paginator = MagicMock()

        mock_session.client.return_value = mock_client
        mock_client.get_paginator.return_value = mock_paginator

        # Simulate generic exception
        mock_paginator.paginate.side_effect = Exception("Network timeout")

        # Act
        result = get_cloudtrail_events(mock_session, "ca-central-1", 24)

        # Assert - Should return empty list and log warning (not raise exception)
        assert result == []

    @patch("cartography.intel.aws.cloudtrail_management_events.get_botocore_config")
    def test_get_cloudtrail_events_region_parameter_usage(self, mock_botocore_config):
        """Test that the region parameter is correctly passed to the boto3 client."""
        # Arrange
        mock_session = MagicMock(spec=boto3.Session)
        mock_client = MagicMock()
        mock_paginator = MagicMock()

        mock_session.client.return_value = mock_client
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [LOOKUP_EVENTS_EMPTY_RESPONSE]

        test_region = "eu-central-1"

        # Act
        get_cloudtrail_events(mock_session, test_region, 24)

        # Assert - Verify region is passed correctly
        mock_session.client.assert_called_once_with(
            "cloudtrail",
            region_name=test_region,
            config=mock_botocore_config.return_value,
        )

    @patch("cartography.intel.aws.cloudtrail_management_events.get_botocore_config")
    def test_get_cloudtrail_events_filters_sts_events_only(self, mock_botocore_config):
        """Test that the function correctly filters for STS events only."""
        # Arrange
        mock_session = MagicMock(spec=boto3.Session)
        mock_client = MagicMock()
        mock_paginator = MagicMock()

        mock_session.client.return_value = mock_client
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [LOOKUP_EVENTS_SINGLE_PAGE_RESPONSE]

        # Act
        get_cloudtrail_events(mock_session, "us-east-1", 24)

        # Assert - Verify STS event filtering
        call_args = mock_paginator.paginate.call_args
        lookup_attributes = call_args[1]["LookupAttributes"]

        assert len(lookup_attributes) == 1
        assert lookup_attributes[0]["AttributeKey"] == "EventSource"
        assert lookup_attributes[0]["AttributeValue"] == "sts.amazonaws.com"

    @patch("cartography.intel.aws.cloudtrail_management_events.get_botocore_config")
    def test_get_cloudtrail_events_pagination_config(self, mock_botocore_config):
        """Test that pagination configuration is set correctly."""
        # Arrange
        mock_session = MagicMock(spec=boto3.Session)
        mock_client = MagicMock()
        mock_paginator = MagicMock()

        mock_session.client.return_value = mock_client
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [LOOKUP_EVENTS_EMPTY_RESPONSE]

        # Act
        get_cloudtrail_events(mock_session, "us-east-1", 24)

        # Assert - Verify pagination configuration
        call_args = mock_paginator.paginate.call_args
        pagination_config = call_args[1]["PaginationConfig"]

        assert pagination_config["MaxItems"] == 10000
        assert pagination_config["PageSize"] == 50


class TestTransformCloudTrailEvents:
    """Test suite for transform_cloudtrail_events_to_role_assumptions function."""

    def test_transform_cloudtrail_events_success_all_types(self):
        """Test successful transformation of all STS event types."""
        # Arrange
        events = [
            STS_ASSUME_ROLE_EVENT,
            STS_ASSUME_ROLE_WITH_SAML_EVENT,
            STS_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT,
        ]
        region = "us-east-1"
        account_id = "123456789012"

        # Act
        result = transform_cloudtrail_events_to_role_assumptions(
            events, region, account_id
        )

        # Assert
        assert len(result) == 3
        assert result == EXPECTED_TRANSFORMED_ROLE_ASSUMPTIONS

        # Verify each transformation individually
        assert result[0] == EXPECTED_ROLE_ASSUMPTION_FROM_STS_ASSUME_ROLE
        assert result[1] == EXPECTED_ROLE_ASSUMPTION_FROM_SAML
        assert result[2] == EXPECTED_ROLE_ASSUMPTION_FROM_WEB_IDENTITY

    def test_transform_single_assume_role_event(self):
        """Test transformation of a single AssumeRole event."""
        # Arrange
        events = [STS_ASSUME_ROLE_EVENT]
        region = "us-east-1"
        account_id = "123456789012"

        # Act
        result = transform_cloudtrail_events_to_role_assumptions(
            events, region, account_id
        )

        # Assert
        assert len(result) == 1
        assumption = result[0]

        assert (
            assumption["SourcePrincipal"] == "arn:aws:iam::123456789012:user/john.doe"
        )
        assert (
            assumption["DestinationPrincipal"]
            == "arn:aws:iam::987654321098:role/CrossAccountRole"
        )
        assert assumption["Action"] == "AssumeRole"
        assert assumption["EventId"] == "f47ac10b-58cc-4372-a567-0e02b2c3d479"
        assert assumption["AccountId"] == account_id
        assert assumption["AwsRegion"] == "us-east-1"

    def test_transform_assume_role_with_saml_event(self):
        """Test transformation of AssumeRoleWithSAML event."""
        # Arrange
        events = [STS_ASSUME_ROLE_WITH_SAML_EVENT]
        region = "us-east-1"
        account_id = "123456789012"

        # Act
        result = transform_cloudtrail_events_to_role_assumptions(
            events, region, account_id
        )

        # Assert
        assert len(result) == 1
        assumption = result[0]

        assert (
            assumption["SourcePrincipal"]
            == "arn:aws:sts::123456789012:assumed-role/SAMLRole/jane.smith@company.com"
        )
        assert (
            assumption["DestinationPrincipal"]
            == "arn:aws:iam::123456789012:role/SAMLRole"
        )
        assert assumption["Action"] == "AssumeRoleWithSAML"
        assert assumption["EventId"] == "a1b2c3d4-e5f6-7890-1234-567890abcdef"

    def test_transform_assume_role_with_web_identity_event(self):
        """Test transformation of AssumeRoleWithWebIdentity event."""
        # Arrange
        events = [STS_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT]
        region = "us-west-2"
        account_id = "123456789012"

        # Act
        result = transform_cloudtrail_events_to_role_assumptions(
            events, region, account_id
        )

        # Assert
        assert len(result) == 1
        assumption = result[0]

        assert (
            assumption["SourcePrincipal"]
            == "arn:aws:sts::123456789012:assumed-role/WebIdentityRole/web-session-1642254300"
        )
        assert (
            assumption["DestinationPrincipal"]
            == "arn:aws:iam::123456789012:role/WebIdentityRole"
        )
        assert assumption["Action"] == "AssumeRoleWithWebIdentity"
        assert assumption["AwsRegion"] == "us-west-2"

    def test_transform_filters_non_sts_events(self):
        """Test that non-STS events are filtered out."""
        # Arrange
        events = [
            STS_ASSUME_ROLE_EVENT,
            NON_STS_EVENT,  # This should be filtered out
            STS_ASSUME_ROLE_WITH_SAML_EVENT,
        ]
        region = "us-east-1"
        account_id = "123456789012"

        # Act
        result = transform_cloudtrail_events_to_role_assumptions(
            events, region, account_id
        )

        # Assert
        assert len(result) == 2  # Only 2 STS events should be processed
        assert result[0]["Action"] == "AssumeRole"
        assert result[1]["Action"] == "AssumeRoleWithSAML"

    def test_transform_handles_malformed_events(self):
        """Test that malformed events are handled gracefully."""
        # Arrange
        events = [
            STS_ASSUME_ROLE_EVENT,
            MALFORMED_EVENT,  # This should be skipped
            STS_ASSUME_ROLE_WITH_SAML_EVENT,
        ]
        region = "us-east-1"
        account_id = "123456789012"

        # Act
        result = transform_cloudtrail_events_to_role_assumptions(
            events, region, account_id
        )

        # Assert
        assert len(result) == 2  # Malformed event should be skipped
        assert result[0]["Action"] == "AssumeRole"
        assert result[1]["Action"] == "AssumeRoleWithSAML"

    def test_transform_empty_events_list(self):
        """Test transformation of empty events list."""
        # Arrange
        events = []
        region = "us-east-1"
        account_id = "123456789012"

        # Act
        result = transform_cloudtrail_events_to_role_assumptions(
            events, region, account_id
        )

        # Assert
        assert result == []
        assert len(result) == 0

    def test_transform_includes_additional_context_fields(self):
        """Test that additional context fields are included in the transformation."""
        # Arrange
        events = [STS_ASSUME_ROLE_EVENT]
        region = "us-east-1"
        account_id = "123456789012"

        # Act
        result = transform_cloudtrail_events_to_role_assumptions(
            events, region, account_id
        )

        # Assert
        assert len(result) == 1
        assumption = result[0]

        # Check that all expected fields are present
        expected_fields = [
            "SourcePrincipal",
            "DestinationPrincipal",
            "Action",
            "EventId",
            "EventTime",
            "SourceIPAddress",
            "UserAgent",
            "AwsRegion",
            "AccountId",
            "AssumedRoleArn",
            "PrincipalArn",
            "SessionName",
            "RequestId",
            "RecipientAccountId",
        ]

        for field in expected_fields:
            assert field in assumption

    def test_transform_cross_account_role_assumption(self):
        """Test that cross-account role assumptions are correctly identified."""
        # Arrange
        events = [STS_ASSUME_ROLE_EVENT]  # Cross-account assumption
        region = "us-east-1"
        account_id = "123456789012"

        # Act
        result = transform_cloudtrail_events_to_role_assumptions(
            events, region, account_id
        )

        # Assert
        assert len(result) == 1
        assumption = result[0]

        # Source account: 123456789012, Destination account: 987654321098
        assert "123456789012" in assumption["SourcePrincipal"]
        assert "987654321098" in assumption["DestinationPrincipal"]
        assert assumption["RecipientAccountId"] == "987654321098"

    def test_transform_handles_different_regions(self):
        """Test that region parameter is correctly applied."""
        # Arrange
        events = [STS_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT]
        test_region = "ap-southeast-1"
        account_id = "123456789012"

        # Act
        result = transform_cloudtrail_events_to_role_assumptions(
            events, test_region, account_id
        )

        # Assert
        assert len(result) == 1
        assumption = result[0]

        # Event has AwsRegion: 'us-west-2', but if missing it should fallback to test_region
        assert (
            assumption["AwsRegion"] == "us-west-2"
        )  # Should preserve original event region
        assert assumption["AccountId"] == account_id


class TestAggregateRoleAssumptions:
    """Test suite for _aggregate_role_assumptions function."""

    def test_aggregate_single_event(self):
        """Test aggregation of a single role assumption event."""
        # Arrange
        role_assumptions = [EXPECTED_ROLE_ASSUMPTION_FROM_STS_ASSUME_ROLE]

        # Act
        result = _aggregate_role_assumptions(role_assumptions)

        # Assert
        assert len(result) == 1
        aggregated = result[0]

        assert (
            aggregated["source_principal_arn"]
            == "arn:aws:iam::123456789012:user/john.doe"
        )
        assert (
            aggregated["destination_principal_arn"]
            == "arn:aws:iam::987654321098:role/CrossAccountRole"
        )
        assert aggregated["times_used"] == 1
        assert aggregated["first_seen"] == datetime(2024, 1, 15, 10, 30, 15, 123000)
        assert aggregated["last_seen"] == datetime(2024, 1, 15, 10, 30, 15, 123000)
        assert aggregated["lastused"] == datetime(2024, 1, 15, 10, 30, 15, 123000)

    def test_aggregate_multiple_events_same_pair(self):
        """Test aggregation of multiple events for the same (source, destination) pair."""
        # Arrange - Create multiple events with same source/dest but different times
        event1 = {
            "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
            "DestinationPrincipal": "arn:aws:iam::123456789012:role/DataScientist",
            "EventTime": datetime(2024, 1, 15, 10, 0, 0),
            "Action": "AssumeRole",
            "EventId": "event-1",
        }
        event2 = {
            "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
            "DestinationPrincipal": "arn:aws:iam::123456789012:role/DataScientist",
            "EventTime": datetime(2024, 1, 15, 14, 30, 0),
            "Action": "AssumeRole",
            "EventId": "event-2",
        }
        event3 = {
            "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
            "DestinationPrincipal": "arn:aws:iam::123456789012:role/DataScientist",
            "EventTime": datetime(2024, 1, 15, 12, 15, 0),
            "Action": "AssumeRole",
            "EventId": "event-3",
        }

        role_assumptions = [event1, event2, event3]

        # Act
        result = _aggregate_role_assumptions(role_assumptions)

        # Assert
        assert len(result) == 1  # Should aggregate into one relationship
        aggregated = result[0]

        assert (
            aggregated["source_principal_arn"] == "arn:aws:iam::123456789012:user/alice"
        )
        assert (
            aggregated["destination_principal_arn"]
            == "arn:aws:iam::123456789012:role/DataScientist"
        )
        assert aggregated["times_used"] == 3  # Count of events
        assert aggregated["first_seen"] == datetime(
            2024, 1, 15, 10, 0, 0
        )  # Earliest time
        assert aggregated["last_seen"] == datetime(
            2024, 1, 15, 14, 30, 0
        )  # Latest time
        assert aggregated["lastused"] == datetime(
            2024, 1, 15, 14, 30, 0
        )  # Same as last_seen

    def test_aggregate_multiple_events_different_pairs(self):
        """Test aggregation of events for different (source, destination) pairs."""
        # Arrange - Different users and roles
        event1 = {
            "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
            "DestinationPrincipal": "arn:aws:iam::123456789012:role/DataScientist",
            "EventTime": datetime(2024, 1, 15, 10, 0, 0),
            "Action": "AssumeRole",
            "EventId": "event-1",
        }
        event2 = {
            "SourcePrincipal": "arn:aws:iam::123456789012:user/bob",
            "DestinationPrincipal": "arn:aws:iam::123456789012:role/Developer",
            "EventTime": datetime(2024, 1, 15, 11, 0, 0),
            "Action": "AssumeRole",
            "EventId": "event-2",
        }
        event3 = {
            "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
            "DestinationPrincipal": "arn:aws:iam::123456789012:role/Developer",  # Alice also assumes Developer
            "EventTime": datetime(2024, 1, 15, 12, 0, 0),
            "Action": "AssumeRole",
            "EventId": "event-3",
        }

        role_assumptions = [event1, event2, event3]

        # Act
        result = _aggregate_role_assumptions(role_assumptions)

        # Assert
        assert len(result) == 3  # Three unique (source, destination) pairs

        # Sort for consistent testing
        result.sort(
            key=lambda x: (x["source_principal_arn"], x["destination_principal_arn"])
        )

        # Check alice -> DataScientist
        assert (
            result[0]["source_principal_arn"] == "arn:aws:iam::123456789012:user/alice"
        )
        assert (
            result[0]["destination_principal_arn"]
            == "arn:aws:iam::123456789012:role/DataScientist"
        )
        assert result[0]["times_used"] == 1

        # Check alice -> Developer
        assert (
            result[1]["source_principal_arn"] == "arn:aws:iam::123456789012:user/alice"
        )
        assert (
            result[1]["destination_principal_arn"]
            == "arn:aws:iam::123456789012:role/Developer"
        )
        assert result[1]["times_used"] == 1

        # Check bob -> Developer
        assert result[2]["source_principal_arn"] == "arn:aws:iam::123456789012:user/bob"
        assert (
            result[2]["destination_principal_arn"]
            == "arn:aws:iam::123456789012:role/Developer"
        )
        assert result[2]["times_used"] == 1

    def test_aggregate_empty_list(self):
        """Test aggregation of empty role assumptions list."""
        # Arrange
        role_assumptions = []

        # Act
        result = _aggregate_role_assumptions(role_assumptions)

        # Assert
        assert result == []
        assert len(result) == 0

    def test_aggregate_incomplete_events_skipped(self):
        """Test that incomplete events (missing required fields) are skipped."""
        # Arrange
        incomplete_event1 = {
            "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
            # Missing DestinationPrincipal
            "EventTime": datetime(2024, 1, 15, 10, 0, 0),
        }
        incomplete_event2 = {
            # Missing SourcePrincipal
            "DestinationPrincipal": "arn:aws:iam::123456789012:role/DataScientist",
            "EventTime": datetime(2024, 1, 15, 10, 0, 0),
        }
        incomplete_event3 = {
            "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
            "DestinationPrincipal": "arn:aws:iam::123456789012:role/DataScientist",
            # Missing EventTime
        }
        complete_event = {
            "SourcePrincipal": "arn:aws:iam::123456789012:user/bob",
            "DestinationPrincipal": "arn:aws:iam::123456789012:role/Developer",
            "EventTime": datetime(2024, 1, 15, 11, 0, 0),
            "Action": "AssumeRole",
            "EventId": "complete-event",
        }

        role_assumptions = [
            incomplete_event1,
            incomplete_event2,
            incomplete_event3,
            complete_event,
        ]

        # Act
        result = _aggregate_role_assumptions(role_assumptions)

        # Assert - Only the complete event should be processed
        assert len(result) == 1
        assert result[0]["source_principal_arn"] == "arn:aws:iam::123456789012:user/bob"
        assert (
            result[0]["destination_principal_arn"]
            == "arn:aws:iam::123456789012:role/Developer"
        )

    def test_aggregate_mixed_event_types(self):
        """Test aggregation with different STS event types."""
        # Arrange - Use the predefined test data
        role_assumptions = EXPECTED_TRANSFORMED_ROLE_ASSUMPTIONS

        # Act
        result = _aggregate_role_assumptions(role_assumptions)

        # Assert - Each should create a separate aggregated relationship
        assert len(result) == 3

        # Verify each aggregated relationship has correct structure
        for aggregated in result:
            assert "source_principal_arn" in aggregated
            assert "destination_principal_arn" in aggregated
            assert aggregated["times_used"] == 1  # Each is a single event
            assert "first_seen" in aggregated
            assert "last_seen" in aggregated
            assert "lastused" in aggregated
            assert aggregated["lastused"] == aggregated["last_seen"]

    def test_aggregate_with_predefined_multiple_events(self):
        """Test aggregation using predefined test data for multiple events of same pair."""
        # Arrange - Use predefined test data with multiple events for same (source, destination)
        role_assumptions = MULTIPLE_ASSUME_ROLE_EVENTS_SAME_PAIR

        # Act
        result = _aggregate_role_assumptions(role_assumptions)

        # Assert
        assert len(result) == 1  # Should aggregate into single relationship
        aggregated = result[0]

        # Compare against expected aggregated result
        expected = EXPECTED_AGGREGATED_ALICE_DATASCIENTIST
        assert aggregated["source_principal_arn"] == expected["source_principal_arn"]
        assert (
            aggregated["destination_principal_arn"]
            == expected["destination_principal_arn"]
        )
        assert aggregated["times_used"] == expected["times_used"]
        assert aggregated["first_seen"] == expected["first_seen"]
        assert aggregated["last_seen"] == expected["last_seen"]
        assert aggregated["lastused"] == expected["lastused"]

    def test_aggregate_cross_account_and_different_source_types(self):
        """Test aggregation with cross-account events and different source types."""
        # Arrange - Use predefined test data with different source types
        role_assumptions = CROSS_ACCOUNT_ROLE_ASSUMPTION_EVENTS

        # Act
        result = _aggregate_role_assumptions(role_assumptions)

        # Assert
        assert len(result) == 3  # Each should be a separate relationship

        # Sort for consistent testing
        result.sort(key=lambda x: x["source_principal_arn"])

        # Check Role -> Role (appears first alphabetically)
        assert (
            result[0]["source_principal_arn"]
            == "arn:aws:iam::123456789012:role/ApplicationRole"
        )
        assert (
            result[0]["destination_principal_arn"]
            == "arn:aws:iam::123456789012:role/DataAccessRole"
        )

        # Check User -> CrossAccountRole
        assert (
            result[1]["source_principal_arn"]
            == "arn:aws:iam::123456789012:user/service-account"
        )
        assert (
            result[1]["destination_principal_arn"]
            == "arn:aws:iam::987654321098:role/CrossAccountRole"
        )

        # Check Federated -> Role
        assert (
            result[2]["source_principal_arn"]
            == "arn:aws:sts::123456789012:federated-user/external-user"
        )
        assert (
            result[2]["destination_principal_arn"]
            == "arn:aws:iam::123456789012:role/FederatedRole"
        )

        # Verify all have single usage count
        for aggregated in result:
            assert aggregated["times_used"] == 1

    def test_aggregate_with_incomplete_events_using_test_data(self):
        """Test aggregation with incomplete events using predefined test data."""
        # Arrange - Mix complete and incomplete events
        complete_event = EXPECTED_ROLE_ASSUMPTION_FROM_STS_ASSUME_ROLE
        role_assumptions = INCOMPLETE_ROLE_ASSUMPTION_EVENTS + [complete_event]

        # Act
        result = _aggregate_role_assumptions(role_assumptions)

        # Assert - Only the complete event should be processed
        assert len(result) == 1
        assert result[0]["source_principal_arn"] == complete_event["SourcePrincipal"]
        assert (
            result[0]["destination_principal_arn"]
            == complete_event["DestinationPrincipal"]
        )


class TestLoadRoleAssumptions:
    """Test suite for load_role_assumptions function."""

    def test_load_role_assumptions_success(self):
        """Test successful loading of role assumptions into Neo4j."""
        # Arrange
        mock_session = MagicMock()
        role_assumptions = [
            {
                "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
                "DestinationPrincipal": "arn:aws:iam::123456789012:role/DataScientist",
                "EventTime": datetime(2024, 1, 15, 10, 0, 0),
                "Action": "AssumeRole",
                "EventId": "event-1",
            }
        ]
        region = "us-east-1"
        account_id = "123456789012"
        update_tag = 1705312345

        # Act
        load_role_assumptions(
            mock_session, role_assumptions, region, account_id, update_tag
        )

        # Assert - Verify Neo4j session was called with correct query
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args

        # Check that the Cypher query contains expected patterns
        query = call_args[0][0]
        assert "UNWIND $assumptions AS assumption" in query
        assert "CALL {" in query  # UNION subquery for source node discovery
        assert "MATCH (source:AWSUser" in query
        assert "MATCH (source:AWSRole" in query
        assert "MATCH (source:AWSPrincipal" in query
        assert (
            "MERGE (dest:AWSRole {arn: assumption.destination_principal_arn})" in query
        )
        assert "MERGE (source_node)-[rel:ASSUMED_ROLE]->(dest)" in query

        # Check parameters
        params = call_args[1]
        assert "assumptions" in params
        assert "aws_update_tag" in params
        assert params["aws_update_tag"] == update_tag

        # Check aggregated data structure
        aggregated_data = params["assumptions"]
        assert len(aggregated_data) == 1
        assert (
            aggregated_data[0]["source_principal_arn"]
            == "arn:aws:iam::123456789012:user/alice"
        )
        assert (
            aggregated_data[0]["destination_principal_arn"]
            == "arn:aws:iam::123456789012:role/DataScientist"
        )
        assert aggregated_data[0]["times_used"] == 1

    def test_load_role_assumptions_empty_list(self):
        """Test that empty role assumptions list is handled gracefully."""
        # Arrange
        mock_session = MagicMock()
        role_assumptions = []

        # Act
        load_role_assumptions(
            mock_session, role_assumptions, "us-east-1", "123456789012", 1705312345
        )

        # Assert - Should return early without calling Neo4j
        mock_session.run.assert_not_called()

    def test_load_role_assumptions_complex_aggregation(self):
        """Test loading with complex aggregation scenarios."""
        # Arrange
        mock_session = MagicMock()

        # Multiple events that should aggregate
        role_assumptions = [
            {
                "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
                "DestinationPrincipal": "arn:aws:iam::123456789012:role/DataScientist",
                "EventTime": datetime(2024, 1, 15, 10, 0, 0),
                "Action": "AssumeRole",
                "EventId": "event-1",
            },
            {
                "SourcePrincipal": "arn:aws:iam::123456789012:user/alice",
                "DestinationPrincipal": "arn:aws:iam::123456789012:role/DataScientist",
                "EventTime": datetime(2024, 1, 15, 14, 0, 0),
                "Action": "AssumeRole",
                "EventId": "event-2",
            },
            {
                "SourcePrincipal": "arn:aws:iam::123456789012:user/bob",
                "DestinationPrincipal": "arn:aws:iam::123456789012:role/Developer",
                "EventTime": datetime(2024, 1, 15, 12, 0, 0),
                "Action": "AssumeRole",
                "EventId": "event-3",
            },
        ]

        # Act
        load_role_assumptions(
            mock_session, role_assumptions, "us-east-1", "123456789012", 1705312345
        )

        # Assert
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        params = call_args[1]

        # Should have 2 aggregated relationships (alice->DataScientist aggregated, bob->Developer separate)
        aggregated_data = params["assumptions"]
        assert len(aggregated_data) == 2

        # Find alice's aggregated relationship
        alice_relationship = next(
            (
                item
                for item in aggregated_data
                if item["source_principal_arn"]
                == "arn:aws:iam::123456789012:user/alice"
            ),
            None,
        )
        assert alice_relationship is not None
        assert alice_relationship["times_used"] == 2  # Two events aggregated
        assert alice_relationship["first_seen"] == datetime(
            2024, 1, 15, 10, 0, 0
        )  # Earlier time
        assert alice_relationship["last_seen"] == datetime(
            2024, 1, 15, 14, 0, 0
        )  # Later time

        # Find bob's relationship
        bob_relationship = next(
            (
                item
                for item in aggregated_data
                if item["source_principal_arn"] == "arn:aws:iam::123456789012:user/bob"
            ),
            None,
        )
        assert bob_relationship is not None
        assert bob_relationship["times_used"] == 1  # Single event

    def test_load_role_assumptions_cypher_query_structure(self):
        """Test that the generated Cypher query has the correct structure for temporal aggregation."""
        # Arrange
        mock_session = MagicMock()
        role_assumptions = [EXPECTED_ROLE_ASSUMPTION_FROM_STS_ASSUME_ROLE]

        # Act
        load_role_assumptions(
            mock_session, role_assumptions, "us-east-1", "123456789012", 1705312345
        )

        # Assert - Check detailed query structure
        call_args = mock_session.run.call_args
        query = call_args[0][0]

        # Verify temporal aggregation logic is present
        assert "SET rel.lastused = COALESCE(" in query
        assert "CASE WHEN assumption.last_seen >" in query
        assert (
            "rel.times_used = COALESCE(rel.times_used, 0) + assumption.times_used"
            in query
        )
        assert "rel.first_seen = COALESCE(" in query
        assert "CASE WHEN assumption.first_seen <" in query
        assert "rel.last_seen = COALESCE(" in query
        assert "rel.lastupdated = $aws_update_tag" in query

        # Verify UNION structure for source node discovery
        assert "UNION" in query
        assert query.count("UNION") == 2  # Two UNION clauses for three branches

    def test_load_role_assumptions_with_real_test_data(self):
        """Test loading using the predefined test data."""
        # Arrange
        mock_session = MagicMock()
        role_assumptions = EXPECTED_TRANSFORMED_ROLE_ASSUMPTIONS

        # Act
        load_role_assumptions(
            mock_session, role_assumptions, "us-east-1", "123456789012", 1705312345
        )

        # Assert
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        params = call_args[1]

        # Should have 3 aggregated relationships (one for each different assumption)
        aggregated_data = params["assumptions"]
        assert len(aggregated_data) == 3

        # Verify each has the required structure
        for assumption in aggregated_data:
            assert "source_principal_arn" in assumption
            assert "destination_principal_arn" in assumption
            assert "times_used" in assumption
            assert "first_seen" in assumption
            assert "last_seen" in assumption
            assert "lastused" in assumption

            # Verify lastused equals last_seen
            assert assumption["lastused"] == assumption["last_seen"]

    def test_load_role_assumptions_query_patterns_comprehensive(self):
        """Test that all expected Cypher query patterns are present."""
        # Arrange
        mock_session = MagicMock()
        role_assumptions = [EXPECTED_ROLE_ASSUMPTION_FROM_STS_ASSUME_ROLE]

        # Act
        load_role_assumptions(
            mock_session, role_assumptions, "us-east-1", "123456789012", 1705312345
        )

        # Assert - Check all expected patterns are in the query
        call_args = mock_session.run.call_args
        query = call_args[0][0]

        for pattern_name, pattern in EXPECTED_CYPHER_QUERY_PATTERNS.items():
            assert (
                pattern in query
            ), f"Expected pattern '{pattern_name}' not found in query"

    def test_load_role_assumptions_with_multiple_events_same_pair(self):
        """Test loading with multiple events that should aggregate into one relationship."""
        # Arrange
        mock_session = MagicMock()
        role_assumptions = MULTIPLE_ASSUME_ROLE_EVENTS_SAME_PAIR

        # Act
        load_role_assumptions(
            mock_session, role_assumptions, "us-east-1", "123456789012", 1705312345
        )

        # Assert
        call_args = mock_session.run.call_args
        params = call_args[1]

        # Should have 1 aggregated relationship (all events for same pair)
        aggregated_data = params["assumptions"]
        assert len(aggregated_data) == 1

        # Verify aggregation matches expected
        aggregated = aggregated_data[0]
        expected = EXPECTED_AGGREGATED_ALICE_DATASCIENTIST
        assert aggregated == expected

    def test_load_role_assumptions_with_cross_account_events(self):
        """Test loading with cross-account role assumptions."""
        # Arrange
        mock_session = MagicMock()
        role_assumptions = CROSS_ACCOUNT_ROLE_ASSUMPTION_EVENTS

        # Act
        load_role_assumptions(
            mock_session, role_assumptions, "us-east-1", "123456789012", 1705312345
        )

        # Assert
        call_args = mock_session.run.call_args
        params = call_args[1]

        # Should have 3 separate relationships (different source-destination pairs)
        aggregated_data = params["assumptions"]
        assert len(aggregated_data) == 3

        # Check that we have the expected ARN patterns
        source_arns = {item["source_principal_arn"] for item in aggregated_data}
        dest_arns = {item["destination_principal_arn"] for item in aggregated_data}

        # Verify we have different source types
        assert "arn:aws:iam::123456789012:user/service-account" in source_arns  # User
        assert "arn:aws:iam::123456789012:role/ApplicationRole" in source_arns  # Role
        assert (
            "arn:aws:sts::123456789012:federated-user/external-user" in source_arns
        )  # Federated

        # Verify we have cross-account destination
        assert "arn:aws:iam::987654321098:role/CrossAccountRole" in dest_arns

    def test_load_role_assumptions_parameter_validation(self):
        """Test that the correct parameters are passed to Neo4j session."""
        # Arrange
        mock_session = MagicMock()
        role_assumptions = [EXPECTED_ROLE_ASSUMPTION_FROM_STS_ASSUME_ROLE]
        region = "eu-west-1"
        account_id = "999888777666"
        update_tag = 1234567890

        # Act
        load_role_assumptions(
            mock_session, role_assumptions, region, account_id, update_tag
        )

        # Assert - Verify exact parameter values
        call_args = mock_session.run.call_args
        params = call_args[1]

        assert params["aws_update_tag"] == update_tag
        assert "assumptions" in params
        assert isinstance(params["assumptions"], list)
        assert len(params["assumptions"]) == 1

        # Verify the aggregated assumption structure
        assumption = params["assumptions"][0]
        assert (
            assumption["source_principal_arn"]
            == "arn:aws:iam::123456789012:user/john.doe"
        )
        assert (
            assumption["destination_principal_arn"]
            == "arn:aws:iam::987654321098:role/CrossAccountRole"
        )
        assert assumption["times_used"] == 1

    def test_load_role_assumptions_handles_incomplete_data_gracefully(self):
        """Test that incomplete events are filtered out during aggregation."""
        # Arrange
        mock_session = MagicMock()

        # Mix incomplete and complete events
        complete_event = EXPECTED_ROLE_ASSUMPTION_FROM_STS_ASSUME_ROLE
        role_assumptions = INCOMPLETE_ROLE_ASSUMPTION_EVENTS + [complete_event]

        # Act
        load_role_assumptions(
            mock_session, role_assumptions, "us-east-1", "123456789012", 1705312345
        )

        # Assert - Only complete event should be processed
        call_args = mock_session.run.call_args
        params = call_args[1]

        aggregated_data = params["assumptions"]
        assert len(aggregated_data) == 1  # Only the complete event
        assert (
            aggregated_data[0]["source_principal_arn"]
            == complete_event["SourcePrincipal"]
        )
        assert (
            aggregated_data[0]["destination_principal_arn"]
            == complete_event["DestinationPrincipal"]
        )


class TestSyncFunction:
    """Test suite for the main sync orchestration function."""

    @patch("cartography.intel.aws.cloudtrail_management_events.get_cloudtrail_events")
    @patch(
        "cartography.intel.aws.cloudtrail_management_events.transform_cloudtrail_events_to_role_assumptions"
    )
    @patch("cartography.intel.aws.cloudtrail_management_events.load_role_assumptions")
    def test_sync_success_with_lookback_hours(
        self, mock_load, mock_transform, mock_get_events
    ):
        """Test successful sync with lookback hours specified."""
        # Arrange
        mock_neo4j_session = MagicMock()
        mock_boto3_session = MagicMock()
        regions = ["us-east-1", "us-west-2"]
        account_id = "123456789012"
        update_tag = 1705312345
        common_job_parameters = {
            "aws_cloudtrail_management_events_lookback_hours": 24,
            "UPDATE_TAG": update_tag,
        }

        # Mock return values
        mock_events = [STS_ASSUME_ROLE_EVENT, STS_ASSUME_ROLE_WITH_SAML_EVENT]
        mock_role_assumptions = [EXPECTED_ROLE_ASSUMPTION_FROM_STS_ASSUME_ROLE]

        mock_get_events.return_value = mock_events
        mock_transform.return_value = mock_role_assumptions

        # Act
        sync(
            neo4j_session=mock_neo4j_session,
            boto3_session=mock_boto3_session,
            regions=regions,
            current_aws_account_id=account_id,
            update_tag=update_tag,
            common_job_parameters=common_job_parameters,
        )

        # Assert - Verify all components were called correctly
        assert mock_get_events.call_count == 2  # Called for each region
        assert mock_transform.call_count == 2  # Called for each region
        mock_load.assert_called_once()

        # Verify get_cloudtrail_events calls
        expected_calls = [
            call(
                boto3_session=mock_boto3_session, region="us-east-1", lookback_hours=24
            ),
            call(
                boto3_session=mock_boto3_session, region="us-west-2", lookback_hours=24
            ),
        ]
        mock_get_events.assert_has_calls(expected_calls, any_order=True)

        # Verify transform calls
        transform_calls = [
            call(
                events=mock_events,
                region="us-east-1",
                current_aws_account_id=account_id,
            ),
            call(
                events=mock_events,
                region="us-west-2",
                current_aws_account_id=account_id,
            ),
        ]
        mock_transform.assert_has_calls(transform_calls, any_order=True)

        # Verify load call
        load_call_args = mock_load.call_args
        assert load_call_args[1]["neo4j_session"] == mock_neo4j_session
        assert load_call_args[1]["region"] == "all"  # Cross-region aggregation
        assert load_call_args[1]["current_aws_account_id"] == account_id
        assert load_call_args[1]["aws_update_tag"] == update_tag

        # Verify role assumptions were aggregated from all regions
        role_assumptions_arg = load_call_args[1]["role_assumptions"]
        assert len(role_assumptions_arg) == 2  # One from each region

    def test_sync_skipped_when_no_lookback_hours(self):
        """Test that sync is skipped when no lookback hours are specified."""
        # Arrange
        mock_neo4j_session = MagicMock()
        mock_boto3_session = MagicMock()
        common_job_parameters = {
            "UPDATE_TAG": 1705312345,
            # No aws_cloudtrail_management_events_lookback_hours specified
        }

        # Act
        with patch(
            "cartography.intel.aws.cloudtrail_management_events.get_cloudtrail_events"
        ) as mock_get_events:
            sync(
                neo4j_session=mock_neo4j_session,
                boto3_session=mock_boto3_session,
                regions=["us-east-1"],
                current_aws_account_id="123456789012",
                update_tag=1705312345,
                common_job_parameters=common_job_parameters,
            )

        # Assert - No CloudTrail API calls should be made
        mock_get_events.assert_not_called()

    def test_sync_skipped_when_lookback_hours_is_none(self):
        """Test that sync is skipped when lookback hours is explicitly None."""
        # Arrange
        mock_neo4j_session = MagicMock()
        mock_boto3_session = MagicMock()
        common_job_parameters = {
            "aws_cloudtrail_management_events_lookback_hours": None,
            "UPDATE_TAG": 1705312345,
        }

        # Act
        with patch(
            "cartography.intel.aws.cloudtrail_management_events.get_cloudtrail_events"
        ) as mock_get_events:
            sync(
                neo4j_session=mock_neo4j_session,
                boto3_session=mock_boto3_session,
                regions=["us-east-1"],
                current_aws_account_id="123456789012",
                update_tag=1705312345,
                common_job_parameters=common_job_parameters,
            )

        # Assert - No CloudTrail API calls should be made
        mock_get_events.assert_not_called()

    @patch("cartography.intel.aws.cloudtrail_management_events.get_cloudtrail_events")
    @patch(
        "cartography.intel.aws.cloudtrail_management_events.transform_cloudtrail_events_to_role_assumptions"
    )
    @patch("cartography.intel.aws.cloudtrail_management_events.load_role_assumptions")
    def test_sync_continues_on_region_failure(
        self, mock_load, mock_transform, mock_get_events
    ):
        """Test that sync continues processing other regions when one region fails."""
        # Arrange
        mock_neo4j_session = MagicMock()
        mock_boto3_session = MagicMock()
        regions = ["us-east-1", "us-west-2", "eu-west-1"]
        account_id = "123456789012"
        update_tag = 1705312345
        common_job_parameters = {
            "aws_cloudtrail_management_events_lookback_hours": 24,
            "UPDATE_TAG": update_tag,
        }

        # Mock get_cloudtrail_events to fail on second region
        mock_events = [STS_ASSUME_ROLE_EVENT]
        mock_role_assumptions = [EXPECTED_ROLE_ASSUMPTION_FROM_STS_ASSUME_ROLE]

        mock_get_events.side_effect = [
            mock_events,  # Success for us-east-1
            Exception("Access denied for us-west-2"),  # Failure for us-west-2
            mock_events,  # Success for eu-west-1
        ]
        mock_transform.return_value = mock_role_assumptions

        # Act
        sync(
            neo4j_session=mock_neo4j_session,
            boto3_session=mock_boto3_session,
            regions=regions,
            current_aws_account_id=account_id,
            update_tag=update_tag,
            common_job_parameters=common_job_parameters,
        )

        # Assert - Should have attempted all 3 regions
        assert mock_get_events.call_count == 3

        # Should have transformed and loaded data from successful regions only
        assert mock_transform.call_count == 2  # Only successful regions
        mock_load.assert_called_once()

        # Verify the aggregated role assumptions include data from successful regions
        load_call_args = mock_load.call_args
        role_assumptions_arg = load_call_args[1]["role_assumptions"]
        assert len(role_assumptions_arg) == 2  # From 2 successful regions

    @patch("cartography.intel.aws.cloudtrail_management_events.get_cloudtrail_events")
    @patch(
        "cartography.intel.aws.cloudtrail_management_events.transform_cloudtrail_events_to_role_assumptions"
    )
    @patch("cartography.intel.aws.cloudtrail_management_events.load_role_assumptions")
    def test_sync_with_no_events_found(
        self, mock_load, mock_transform, mock_get_events
    ):
        """Test sync behavior when no CloudTrail events are found."""
        # Arrange
        mock_neo4j_session = MagicMock()
        mock_boto3_session = MagicMock()
        regions = ["us-east-1"]
        account_id = "123456789012"
        update_tag = 1705312345
        common_job_parameters = {
            "aws_cloudtrail_management_events_lookback_hours": 72,
            "UPDATE_TAG": update_tag,
        }

        # Mock empty results
        mock_get_events.return_value = []
        mock_transform.return_value = []

        # Act
        sync(
            neo4j_session=mock_neo4j_session,
            boto3_session=mock_boto3_session,
            regions=regions,
            current_aws_account_id=account_id,
            update_tag=update_tag,
            common_job_parameters=common_job_parameters,
        )

        # Assert - Functions should be called but no data loaded
        mock_get_events.assert_called_once()
        mock_transform.assert_called_once()
        mock_load.assert_not_called()  # Should not load empty data

    @patch("cartography.intel.aws.cloudtrail_management_events.get_cloudtrail_events")
    @patch(
        "cartography.intel.aws.cloudtrail_management_events.transform_cloudtrail_events_to_role_assumptions"
    )
    @patch("cartography.intel.aws.cloudtrail_management_events.load_role_assumptions")
    def test_sync_parameter_passing(self, mock_load, mock_transform, mock_get_events):
        """Test that sync function passes parameters correctly to sub-functions."""
        # Arrange
        mock_neo4j_session = MagicMock()
        mock_boto3_session = MagicMock()
        regions = ["eu-central-1"]
        account_id = "999888777666"
        update_tag = 1234567890
        lookback_hours = 168  # 7 days
        common_job_parameters = {
            "aws_cloudtrail_management_events_lookback_hours": lookback_hours,
            "UPDATE_TAG": update_tag,
        }

        # Mock return values
        mock_events = [STS_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT]
        mock_role_assumptions = [EXPECTED_ROLE_ASSUMPTION_FROM_WEB_IDENTITY]

        mock_get_events.return_value = mock_events
        mock_transform.return_value = mock_role_assumptions

        # Act
        sync(
            neo4j_session=mock_neo4j_session,
            boto3_session=mock_boto3_session,
            regions=regions,
            current_aws_account_id=account_id,
            update_tag=update_tag,
            common_job_parameters=common_job_parameters,
        )

        # Assert - Verify exact parameter values passed to sub-functions
        mock_get_events.assert_called_once_with(
            boto3_session=mock_boto3_session,
            region="eu-central-1",
            lookback_hours=lookback_hours,
        )

        mock_transform.assert_called_once_with(
            events=mock_events,
            region="eu-central-1",
            current_aws_account_id=account_id,
        )

        mock_load.assert_called_once_with(
            neo4j_session=mock_neo4j_session,
            role_assumptions=mock_role_assumptions,
            region="all",
            current_aws_account_id=account_id,
            aws_update_tag=update_tag,
        )
