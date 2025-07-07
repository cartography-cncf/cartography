from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.aws.cloudtrail_management_events import (
    _aggregate_role_assumptions,
)
from cartography.intel.aws.cloudtrail_management_events import load_role_assumptions
from cartography.intel.aws.cloudtrail_management_events import sync
from cartography.intel.aws.cloudtrail_management_events import (
    transform_cloudtrail_events_to_role_assumptions,
)
from tests.data.aws.cloudtrail_management_events import UNIT_TEST_AGGREGATION_EVENTS
from tests.data.aws.cloudtrail_management_events import UNIT_TEST_ASSUME_ROLE_EVENT
from tests.data.aws.cloudtrail_management_events import UNIT_TEST_DIFFERENT_PAIRS_EVENTS
from tests.data.aws.cloudtrail_management_events import (
    UNIT_TEST_EXPECTED_AGGREGATED_RESULT,
)
from tests.data.aws.cloudtrail_management_events import (
    UNIT_TEST_EXPECTED_DIFFERENT_PAIRS,
)
from tests.data.aws.cloudtrail_management_events import UNIT_TEST_MOCK_ASSUMPTIONS
from tests.data.aws.cloudtrail_management_events import UNIT_TEST_MOCK_EVENTS
from tests.data.aws.cloudtrail_management_events import UNIT_TEST_MULTIPLE_STS_EVENTS
from tests.data.aws.cloudtrail_management_events import UNIT_TEST_SIMPLE_ROLE_ASSUMPTION


class TestCloudTrailEventTransformation:
    """Test that CloudTrail events are correctly transformed into role assumption records."""

    def test_transforms_assume_role_events_to_standardized_format(self):
        """
        Tests Raw CloudTrail AssumeRole events are converted to standardized
        role assumption records with all required fields.
        """
        # Arrange: CloudTrail event from lookup_events API
        cloudtrail_events = [UNIT_TEST_ASSUME_ROLE_EVENT]

        # Act: Transform CloudTrail events to role assumptions
        role_assumptions = transform_cloudtrail_events_to_role_assumptions(
            events=cloudtrail_events,
            region="us-east-1",
            current_aws_account_id="123456789012",
        )

        # Assert: Properly structured role assumption record created
        assert len(role_assumptions) == 1
        assumption = role_assumptions[0]

        assert (
            assumption["SourcePrincipal"] == "arn:aws:iam::123456789012:user/john.doe"
        )
        assert (
            assumption["DestinationPrincipal"]
            == "arn:aws:iam::987654321098:role/ApplicationRole"
        )
        assert assumption["Action"] == "AssumeRole"
        assert assumption["EventTime"] == "2024-01-15T10:30:15.123000"
        assert assumption["EventId"] == "test-event-123"

    def test_handles_different_sts_event_types(self):
        """
        Test that all STS role assumption event types (AssumeRole, AssumeRoleWithSAML,
        AssumeRoleWithWebIdentity) are properly transformed.
        """
        # Arrange: Different types of STS events
        cloudtrail_events = UNIT_TEST_MULTIPLE_STS_EVENTS

        # Act: Transform all event types
        role_assumptions = transform_cloudtrail_events_to_role_assumptions(
            events=cloudtrail_events,
            region="us-east-1",
            current_aws_account_id="123456789012",
        )

        # Assert: All event types properly transformed
        assert len(role_assumptions) == 3

        actions = [assumption["Action"] for assumption in role_assumptions]
        assert "AssumeRole" in actions
        assert "AssumeRoleWithSAML" in actions
        assert "AssumeRoleWithWebIdentity" in actions

        destinations = [
            assumption["DestinationPrincipal"] for assumption in role_assumptions
        ]
        assert "arn:aws:iam::123456789012:role/AppRole" in destinations
        assert "arn:aws:iam::123456789012:role/SAMLRole" in destinations
        assert "arn:aws:iam::123456789012:role/WebRole" in destinations


class TestRoleAssumptionAggregation:
    """Test that role assumption events are properly aggregated for analytics."""

    def test_aggregates_multiple_events_for_same_principal_role_pair(self):
        """
        Test that multiple role assumption events for the same (source, destination)
        pair are aggregated into a single record with usage analytics.
        """
        # Arrange: Multiple events for same principal/role pair
        role_assumptions = UNIT_TEST_AGGREGATION_EVENTS

        # Act: Aggregate the role assumptions
        aggregated = _aggregate_role_assumptions(role_assumptions)

        # Assert: Single aggregated record with usage analytics
        assert len(aggregated) == 1

        agg_record = aggregated[0]
        expected = UNIT_TEST_EXPECTED_AGGREGATED_RESULT
        assert agg_record["source_principal_arn"] == expected["source_principal_arn"]
        assert (
            agg_record["destination_principal_arn"]
            == expected["destination_principal_arn"]
        )
        assert agg_record["times_used"] == expected["times_used"]
        assert agg_record["first_seen"] == expected["first_seen"]
        assert agg_record["last_seen"] == expected["last_seen"]
        assert agg_record["lastused"] == expected["lastused"]

    def test_preserves_separate_records_for_different_principal_role_pairs(self):
        """
        Test that different (source, destination) pairs maintain separate aggregated records.
        """
        # Arrange: Events for different principal/role combinations
        role_assumptions = UNIT_TEST_DIFFERENT_PAIRS_EVENTS

        # Act: Aggregate the role assumptions
        aggregated = _aggregate_role_assumptions(role_assumptions)

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


class TestMatchLinkIntegration:
    """Test that aggregated role assumptions are loaded into Neo4j via MatchLink."""

    @patch("cartography.intel.aws.cloudtrail_management_events.load_matchlinks")
    def test_loads_aggregated_role_assumptions_via_matchlink(
        self, mock_load_matchlinks
    ):
        """
        OUTCOME: Aggregated role assumption data is passed to MatchLink loader
        with correct schema and parameters.
        """
        # Arrange: Aggregated role assumption data
        role_assumptions = [UNIT_TEST_SIMPLE_ROLE_ASSUMPTION]

        mock_session = MagicMock()

        # Act: Load role assumptions
        load_role_assumptions(
            neo4j_session=mock_session,
            role_assumptions=role_assumptions,
            region="us-east-1",
            current_aws_account_id="123456789012",
            aws_update_tag=1234567890,
        )

        # Assert: MatchLink called with proper parameters
        mock_load_matchlinks.assert_called_once()
        call_args = mock_load_matchlinks.call_args

        # Verify session and schema
        assert call_args[0][0] == mock_session
        assert call_args[0][1].__class__.__name__ == "AssumedRoleMatchLink"

        # Verify aggregated data passed correctly
        aggregated_data = call_args[0][2]
        assert len(aggregated_data) == 1
        assert (
            aggregated_data[0]["source_principal_arn"]
            == "arn:aws:iam::123456789012:user/alice"
        )
        assert (
            aggregated_data[0]["destination_principal_arn"]
            == "arn:aws:iam::123456789012:role/AppRole"
        )

        # Verify MatchLink kwargs
        assert call_args[1]["lastupdated"] == 1234567890
        assert call_args[1]["_sub_resource_label"] == "AWSAccount"
        assert call_args[1]["_sub_resource_id"] == "123456789012"


class TestSyncOrchestration:
    """Test the main sync function orchestrates the complete workflow."""

    @patch("cartography.intel.aws.cloudtrail_management_events.load_role_assumptions")
    @patch(
        "cartography.intel.aws.cloudtrail_management_events.transform_cloudtrail_events_to_role_assumptions"
    )
    @patch("cartography.intel.aws.cloudtrail_management_events.get_cloudtrail_events")
    @patch("cartography.graph.job.GraphJob.from_matchlink")
    def test_orchestrates_complete_cloudtrail_to_graph_workflow(
        self,
        mock_cleanup_job,
        mock_get_events,
        mock_transform,
        mock_load,
    ):
        """
        OUTCOME: The sync function orchestrates the complete workflow from
        CloudTrail events to Neo4j relationships with proper cleanup.
        """
        # Arrange: Mock the workflow components
        mock_events = UNIT_TEST_MOCK_EVENTS
        mock_assumptions = UNIT_TEST_MOCK_ASSUMPTIONS

        mock_get_events.return_value = mock_events
        mock_transform.return_value = mock_assumptions

        mock_cleanup_instance = MagicMock()
        mock_cleanup_job.return_value = mock_cleanup_instance

        mock_session = MagicMock()
        mock_boto3_session = MagicMock()

        # Act: Run complete sync
        sync(
            neo4j_session=mock_session,
            boto3_session=mock_boto3_session,
            regions=["us-east-1"],
            current_aws_account_id="123456789012",
            update_tag=1234567890,
            common_job_parameters={
                "aws_cloudtrail_management_events_lookback_hours": 24
            },
        )

        # Assert: Complete workflow executed

        # 1. CloudTrail events retrieved
        mock_get_events.assert_called_once_with(
            boto3_session=mock_boto3_session,
            region="us-east-1",
            lookback_hours=24,
        )

        # 2. Events transformed to role assumptions
        mock_transform.assert_called_once_with(
            events=mock_events,
            region="us-east-1",
            current_aws_account_id="123456789012",
        )

        # 3. Role assumptions loaded via MatchLink
        mock_load.assert_called_once_with(
            neo4j_session=mock_session,
            role_assumptions=mock_assumptions,
            region="all",
            current_aws_account_id="123456789012",
            aws_update_tag=1234567890,
        )

        # 4. Cleanup job executed
        mock_cleanup_job.assert_called_once()
        mock_cleanup_instance.run.assert_called_once_with(mock_session)
