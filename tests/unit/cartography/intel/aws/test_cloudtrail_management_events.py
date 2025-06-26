from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import boto3
import pytest
from botocore.exceptions import ClientError

from cartography.intel.aws.cloudtrail_management_events import get_cloudtrail_events, transform_cloudtrail_events_to_role_assumptions
from tests.data.aws.cloudtrail_management_events import (
    EXPECTED_PAGINATED_EVENTS,
    EXPECTED_ROLE_ASSUMPTION_FROM_SAML,
    EXPECTED_ROLE_ASSUMPTION_FROM_STS_ASSUME_ROLE,
    EXPECTED_ROLE_ASSUMPTION_FROM_WEB_IDENTITY,
    EXPECTED_TRANSFORMED_ROLE_ASSUMPTIONS,
    LOOKUP_EVENTS_EMPTY_RESPONSE,
    LOOKUP_EVENTS_RESPONSE_PAGE1,
    LOOKUP_EVENTS_RESPONSE_PAGE2,
    LOOKUP_EVENTS_SINGLE_PAGE_RESPONSE,
    MALFORMED_EVENT,
    NON_STS_EVENT,
    STS_ASSUME_ROLE_EVENT,
    STS_ASSUME_ROLE_WITH_SAML_EVENT,
    STS_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT,
)


class TestGetCloudTrailEvents:
    """Test suite for get_cloudtrail_events function."""

    @patch('cartography.intel.aws.cloudtrail_management_events.get_botocore_config')
    def test_get_cloudtrail_events_success_single_page(self, mock_botocore_config):
        """Test successful retrieval of CloudTrail events in a single page."""
        # Arrange
        mock_session = MagicMock(spec=boto3.Session)
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        
        mock_session.client.return_value = mock_client
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [LOOKUP_EVENTS_SINGLE_PAGE_RESPONSE]
        
        region = 'us-east-1'
        lookback_hours = 24
        
        # Act
        result = get_cloudtrail_events(mock_session, region, lookback_hours)
        
        # Assert - Verify client creation
        mock_session.client.assert_called_once_with(
            'cloudtrail',
            region_name=region,
            config=mock_botocore_config.return_value
        )
        
        # Assert - Verify paginator creation
        mock_client.get_paginator.assert_called_once_with('lookup_events')
        
        # Assert - Verify API call parameters
        expected_end_time = datetime.utcnow()
        expected_start_time = expected_end_time - timedelta(hours=lookback_hours)
        
        mock_paginator.paginate.assert_called_once()
        call_args = mock_paginator.paginate.call_args
        
        assert call_args[1]['LookupAttributes'] == [
            {'AttributeKey': 'EventSource', 'AttributeValue': 'sts.amazonaws.com'}
        ]
        assert call_args[1]['PaginationConfig'] == {
            'MaxItems': 10000,
            'PageSize': 50
        }
        
        # Verify time range (allow small tolerance for test execution time)
        start_time_diff = abs((call_args[1]['StartTime'] - expected_start_time).total_seconds())
        end_time_diff = abs((call_args[1]['EndTime'] - expected_end_time).total_seconds())
        assert start_time_diff < 5  # Allow 5 seconds tolerance
        assert end_time_diff < 5
        
        # Assert - Verify results
        assert len(result) == 3
        assert result[0]['EventName'] == 'AssumeRole'
        assert result[1]['EventName'] == 'AssumeRoleWithSAML'
        assert result[2]['EventName'] == 'AssumeRoleWithWebIdentity'
        assert result == EXPECTED_PAGINATED_EVENTS

    @patch('cartography.intel.aws.cloudtrail_management_events.get_botocore_config')
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
            LOOKUP_EVENTS_RESPONSE_PAGE2
        ]
        
        region = 'us-west-2'
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
        time_diff = call_args[1]['EndTime'] - call_args[1]['StartTime']
        assert abs(time_diff.total_seconds() - (72 * 3600)) < 60  # Allow 1 minute tolerance

    @patch('cartography.intel.aws.cloudtrail_management_events.get_botocore_config')
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
        result = get_cloudtrail_events(mock_session, 'eu-west-1', 12)
        
        # Assert
        assert result == []
        assert len(result) == 0

    @patch('cartography.intel.aws.cloudtrail_management_events.get_botocore_config')
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
        result = get_cloudtrail_events(mock_session, 'us-east-1')
        
        # Assert - Verify default 24 hour time range
        call_args = mock_paginator.paginate.call_args
        time_diff = call_args[1]['EndTime'] - call_args[1]['StartTime']
        assert abs(time_diff.total_seconds() - (24 * 3600)) < 60  # Allow 1 minute tolerance

    @patch('cartography.intel.aws.cloudtrail_management_events.get_botocore_config')
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
                'Error': {
                    'Code': 'AccessDenied',
                    'Message': 'User is not authorized to perform: cloudtrail:LookupEvents'
                }
            },
            operation_name='LookupEvents'
        )
        
        # Act
        result = get_cloudtrail_events(mock_session, 'us-east-1', 24)
        
        # Assert - Should return empty list and log warning (not raise exception)
        assert result == []

    @patch('cartography.intel.aws.cloudtrail_management_events.get_botocore_config')
    def test_get_cloudtrail_events_api_error_invalid_time_range(self, mock_botocore_config):
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
                'Error': {
                    'Code': 'InvalidTimeRangeException',
                    'Message': 'Start time must be before end time'
                }
            },
            operation_name='LookupEvents'
        )
        
        # Act
        result = get_cloudtrail_events(mock_session, 'ap-southeast-1', 24)
        
        # Assert - Should return empty list and log warning (not raise exception)
        assert result == []

    @patch('cartography.intel.aws.cloudtrail_management_events.get_botocore_config')
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
        result = get_cloudtrail_events(mock_session, 'ca-central-1', 24)
        
        # Assert - Should return empty list and log warning (not raise exception)
        assert result == []

    @patch('cartography.intel.aws.cloudtrail_management_events.get_botocore_config')
    def test_get_cloudtrail_events_region_parameter_usage(self, mock_botocore_config):
        """Test that the region parameter is correctly passed to the boto3 client."""
        # Arrange
        mock_session = MagicMock(spec=boto3.Session)
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        
        mock_session.client.return_value = mock_client
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [LOOKUP_EVENTS_EMPTY_RESPONSE]
        
        test_region = 'eu-central-1'
        
        # Act
        get_cloudtrail_events(mock_session, test_region, 24)
        
        # Assert - Verify region is passed correctly
        mock_session.client.assert_called_once_with(
            'cloudtrail',
            region_name=test_region,
            config=mock_botocore_config.return_value
        )

    @patch('cartography.intel.aws.cloudtrail_management_events.get_botocore_config')
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
        get_cloudtrail_events(mock_session, 'us-east-1', 24)
        
        # Assert - Verify STS event filtering
        call_args = mock_paginator.paginate.call_args
        lookup_attributes = call_args[1]['LookupAttributes']
        
        assert len(lookup_attributes) == 1
        assert lookup_attributes[0]['AttributeKey'] == 'EventSource'
        assert lookup_attributes[0]['AttributeValue'] == 'sts.amazonaws.com'

    @patch('cartography.intel.aws.cloudtrail_management_events.get_botocore_config')
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
        get_cloudtrail_events(mock_session, 'us-east-1', 24)
        
        # Assert - Verify pagination configuration
        call_args = mock_paginator.paginate.call_args
        pagination_config = call_args[1]['PaginationConfig']
        
        assert pagination_config['MaxItems'] == 10000
        assert pagination_config['PageSize'] == 50


class TestTransformCloudTrailEvents:
    """Test suite for transform_cloudtrail_events_to_role_assumptions function."""

    def test_transform_cloudtrail_events_success_all_types(self):
        """Test successful transformation of all STS event types."""
        # Arrange
        events = [
            STS_ASSUME_ROLE_EVENT,
            STS_ASSUME_ROLE_WITH_SAML_EVENT,
            STS_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT
        ]
        region = 'us-east-1'
        account_id = '123456789012'
        
        # Act
        result = transform_cloudtrail_events_to_role_assumptions(events, region, account_id)
        
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
        region = 'us-east-1'
        account_id = '123456789012'
        
        # Act
        result = transform_cloudtrail_events_to_role_assumptions(events, region, account_id)
        
        # Assert
        assert len(result) == 1
        assumption = result[0]
        
        assert assumption['SourcePrincipal'] == 'arn:aws:iam::123456789012:user/john.doe'
        assert assumption['DestinationPrincipal'] == 'arn:aws:iam::987654321098:role/CrossAccountRole'
        assert assumption['Action'] == 'AssumeRole'
        assert assumption['EventId'] == 'f47ac10b-58cc-4372-a567-0e02b2c3d479'
        assert assumption['AccountId'] == account_id
        assert assumption['AwsRegion'] == 'us-east-1'

    def test_transform_assume_role_with_saml_event(self):
        """Test transformation of AssumeRoleWithSAML event."""
        # Arrange
        events = [STS_ASSUME_ROLE_WITH_SAML_EVENT]
        region = 'us-east-1'
        account_id = '123456789012'
        
        # Act
        result = transform_cloudtrail_events_to_role_assumptions(events, region, account_id)
        
        # Assert
        assert len(result) == 1
        assumption = result[0]
        
        assert assumption['SourcePrincipal'] == 'arn:aws:sts::123456789012:assumed-role/SAMLRole/jane.smith@company.com'
        assert assumption['DestinationPrincipal'] == 'arn:aws:iam::123456789012:role/SAMLRole'
        assert assumption['Action'] == 'AssumeRoleWithSAML'
        assert assumption['EventId'] == 'a1b2c3d4-e5f6-7890-1234-567890abcdef'

    def test_transform_assume_role_with_web_identity_event(self):
        """Test transformation of AssumeRoleWithWebIdentity event."""
        # Arrange
        events = [STS_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT]
        region = 'us-west-2'
        account_id = '123456789012'
        
        # Act
        result = transform_cloudtrail_events_to_role_assumptions(events, region, account_id)
        
        # Assert
        assert len(result) == 1
        assumption = result[0]
        
        assert assumption['SourcePrincipal'] == 'arn:aws:sts::123456789012:assumed-role/WebIdentityRole/web-session-1642254300'
        assert assumption['DestinationPrincipal'] == 'arn:aws:iam::123456789012:role/WebIdentityRole'
        assert assumption['Action'] == 'AssumeRoleWithWebIdentity'
        assert assumption['AwsRegion'] == 'us-west-2'

    def test_transform_filters_non_sts_events(self):
        """Test that non-STS events are filtered out."""
        # Arrange
        events = [
            STS_ASSUME_ROLE_EVENT,
            NON_STS_EVENT,  # This should be filtered out
            STS_ASSUME_ROLE_WITH_SAML_EVENT
        ]
        region = 'us-east-1'
        account_id = '123456789012'
        
        # Act
        result = transform_cloudtrail_events_to_role_assumptions(events, region, account_id)
        
        # Assert
        assert len(result) == 2  # Only 2 STS events should be processed
        assert result[0]['Action'] == 'AssumeRole'
        assert result[1]['Action'] == 'AssumeRoleWithSAML'

    def test_transform_handles_malformed_events(self):
        """Test that malformed events are handled gracefully."""
        # Arrange
        events = [
            STS_ASSUME_ROLE_EVENT,
            MALFORMED_EVENT,  # This should be skipped
            STS_ASSUME_ROLE_WITH_SAML_EVENT
        ]
        region = 'us-east-1'
        account_id = '123456789012'
        
        # Act
        result = transform_cloudtrail_events_to_role_assumptions(events, region, account_id)
        
        # Assert
        assert len(result) == 2  # Malformed event should be skipped
        assert result[0]['Action'] == 'AssumeRole'
        assert result[1]['Action'] == 'AssumeRoleWithSAML'

    def test_transform_empty_events_list(self):
        """Test transformation of empty events list."""
        # Arrange
        events = []
        region = 'us-east-1'
        account_id = '123456789012'
        
        # Act
        result = transform_cloudtrail_events_to_role_assumptions(events, region, account_id)
        
        # Assert
        assert result == []
        assert len(result) == 0

    def test_transform_includes_additional_context_fields(self):
        """Test that additional context fields are included in the transformation."""
        # Arrange
        events = [STS_ASSUME_ROLE_EVENT]
        region = 'us-east-1'
        account_id = '123456789012'
        
        # Act
        result = transform_cloudtrail_events_to_role_assumptions(events, region, account_id)
        
        # Assert
        assert len(result) == 1
        assumption = result[0]
        
        # Check that all expected fields are present
        expected_fields = [
            'SourcePrincipal', 'DestinationPrincipal', 'Action', 'EventId',
            'EventTime', 'SourceIPAddress', 'UserAgent', 'AwsRegion',
            'AccountId', 'AssumedRoleArn', 'PrincipalArn', 'SessionName',
            'RequestId', 'RecipientAccountId'
        ]
        
        for field in expected_fields:
            assert field in assumption

    def test_transform_cross_account_role_assumption(self):
        """Test that cross-account role assumptions are correctly identified."""
        # Arrange
        events = [STS_ASSUME_ROLE_EVENT]  # Cross-account assumption
        region = 'us-east-1'
        account_id = '123456789012'
        
        # Act
        result = transform_cloudtrail_events_to_role_assumptions(events, region, account_id)
        
        # Assert
        assert len(result) == 1
        assumption = result[0]
        
        # Source account: 123456789012, Destination account: 987654321098
        assert '123456789012' in assumption['SourcePrincipal']
        assert '987654321098' in assumption['DestinationPrincipal']
        assert assumption['RecipientAccountId'] == '987654321098'

    def test_transform_handles_different_regions(self):
        """Test that region parameter is correctly applied."""
        # Arrange
        events = [STS_ASSUME_ROLE_WITH_WEB_IDENTITY_EVENT]
        test_region = 'ap-southeast-1'
        account_id = '123456789012'
        
        # Act
        result = transform_cloudtrail_events_to_role_assumptions(events, test_region, account_id)
        
        # Assert
        assert len(result) == 1
        assumption = result[0]
        
        # Event has AwsRegion: 'us-west-2', but if missing it should fallback to test_region
        assert assumption['AwsRegion'] == 'us-west-2'  # Should preserve original event region
        assert assumption['AccountId'] == account_id 