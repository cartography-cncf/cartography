from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j

from cartography.intel.spacelift.account import sync_account
from cartography.intel.spacelift.ec2_ownership import sync_ec2_ownership
from cartography.intel.spacelift.runs import sync_runs
from tests.data.spacelift.spacelift_data import CLOUDTRAIL_EC2_OWNERSHIP_DATA
from tests.data.spacelift.spacelift_data import RUNS_DATA
from tests.integration.cartography.intel.aws.common import create_test_account

TEST_UPDATE_TAG = 123456789
TEST_SPACELIFT_ACCOUNT_ID = "test-spacelift-account"
TEST_AWS_ACCOUNT_ID = "000000000000"
TEST_AWS_REGION = "us-east-1"
TEST_S3_BUCKET = "test-bucket"
TEST_S3_PREFIX = "cloudtrail-data/"


def _setup_test_infrastructure(neo4j_session: neo4j.Session) -> None:
    """
    Set up common test infrastructure: AWS account and EC2 instances.
    """
    create_test_account(neo4j_session, TEST_AWS_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Create EC2 instances that match CloudTrail event instance IDs
    neo4j_session.run(
        """
        MERGE (i1:EC2Instance{id: 'i-01234567', instanceid: 'i-01234567'})
        ON CREATE SET i1.firstseen = timestamp()
        SET i1.lastupdated = $update_tag

        MERGE (i2:EC2Instance{id: 'i-89abcdef', instanceid: 'i-89abcdef'})
        ON CREATE SET i2.firstseen = timestamp()
        SET i2.lastupdated = $update_tag

        MERGE (a:AWSAccount{id: $aws_id})
        ON CREATE SET a.firstseen = timestamp()
        SET a.lastupdated = $update_tag

        MERGE (a)-[r1:RESOURCE]->(i1)
        ON CREATE SET r1.firstseen = timestamp()
        SET r1.lastupdated = $update_tag

        MERGE (a)-[r2:RESOURCE]->(i2)
        ON CREATE SET r2.firstseen = timestamp()
        SET r2.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
        aws_id=TEST_AWS_ACCOUNT_ID,
    )


def _setup_spacelift_runs(
    neo4j_session: neo4j.Session, mock_get_runs, mock_get_entities
) -> None:
    """
    Set up Spacelift runs using the sync function with mocked API calls.
    """
    # Flatten runs for mock
    mock_runs_flattened: list[dict[str, Any]] = []
    for stack in RUNS_DATA["data"]["stacks"]:
        runs: list[dict[str, Any]] = stack.get("runs", [])  # type: ignore[assignment]
        for run in runs:
            run_copy = dict(run)
            run_copy["stack"] = stack["id"]
            mock_runs_flattened.append(run_copy)
    mock_get_runs.return_value = mock_runs_flattened

    spacelift_session = MagicMock()

    # Create Spacelift account and runs
    sync_account(
        neo4j_session,
        "https://fake.spacelift.io/graphql",
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    sync_runs(
        neo4j_session,
        spacelift_session,
        "https://fake.spacelift.io/graphql",
        TEST_SPACELIFT_ACCOUNT_ID,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "SPACELIFT_ACCOUNT_ID": TEST_SPACELIFT_ACCOUNT_ID,
            "account_id": TEST_SPACELIFT_ACCOUNT_ID,
        },
    )


@patch("cartography.intel.spacelift.account.get_account")
@patch("cartography.intel.spacelift.ec2_ownership.get_ec2_ownership")
@patch("cartography.intel.spacelift.runs.get_runs")
@patch("cartography.intel.spacelift.runs.get_entities")
def test_ec2_ownership_preserves_multiple_events(
    mock_get_entities,
    mock_get_runs,
    mock_get_cloudtrail,
    mock_get_account,
    neo4j_session,
):
    """
    Test that multiple CloudTrail events from the same run to the same instance
    are preserved as separate CloudTrailEvent nodes.

    This is the fix for the bug where subsequent events would overwrite previous ones.
    """
    # Arrange
    mock_get_account.return_value = TEST_SPACELIFT_ACCOUNT_ID
    mock_get_cloudtrail.return_value = CLOUDTRAIL_EC2_OWNERSHIP_DATA
    mock_get_entities.return_value = []

    _setup_test_infrastructure(neo4j_session)
    _setup_spacelift_runs(neo4j_session, mock_get_runs, mock_get_entities)

    # Act
    aws_session = MagicMock()
    sync_ec2_ownership(
        neo4j_session,
        aws_session,
        TEST_S3_BUCKET,
        TEST_S3_PREFIX,
        TEST_UPDATE_TAG,
        TEST_SPACELIFT_ACCOUNT_ID,
    )

    # Assert: Verify that 4 CloudTrailEvent nodes were created (one per CloudTrail event)
    result = neo4j_session.run(
        """
        MATCH (e:CloudTrailEvent)<-[:RESOURCE]-(a:SpaceliftAccount{id: $account_id})
        WHERE e.lastupdated = $update_tag
        RETURN e.id as id, e.run_id as run_id, e.instance_ids as instance_ids,
               e.event_time as event_time, e.event_name as event_name
        ORDER BY e.event_time
        """,
        account_id=TEST_SPACELIFT_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )
    events = result.data()
    assert len(events) == 4, f"Expected 4 CloudTrailEvent nodes, got {len(events)}"

    # Verify that all 3 events from run-1 are preserved (they all mention i-01234567)
    run1_events = [e for e in events if e["run_id"] == "run-1"]
    assert (
        len(run1_events) == 3
    ), f"Expected 3 events from run-1, got {len(run1_events)}"

    # Verify event details
    event_names = [e["event_name"] for e in run1_events]
    assert "DescribeInstances" in event_names
    assert "RunInstances" in event_names
    assert event_names.count("DescribeInstances") == 2  # Two DescribeInstances events

    # Verify that events use CloudTrail's native eventid as their ID
    event_ids = [e["id"] for e in events]
    assert "event-uuid-1" in event_ids
    assert "event-uuid-2" in event_ids
    assert "event-uuid-3" in event_ids
    assert "event-uuid-4" in event_ids

    # Assert: Verify relationships from CloudTrailEvent to SpaceliftRun
    # Each CloudTrailEvent should connect to its SpaceliftRun
    result = neo4j_session.run(
        """
        MATCH (e:CloudTrailEvent)<-[:RESOURCE]-(:SpaceliftAccount{id: $account_id})
        WHERE e.lastupdated = $update_tag
        MATCH (e)-[r:FROM_RUN]->(:SpaceliftRun)
        RETURN count(r) as count
        """,
        account_id=TEST_SPACELIFT_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )
    from_run_count = result.single()["count"]
    assert (
        from_run_count == 4
    ), f"Expected 4 FROM_RUN relationships, got {from_run_count}"

    # Assert: Verify relationships from CloudTrailEvent to EC2Instance
    # Each event creates relationships to all instances it mentions
    result = neo4j_session.run(
        """
        MATCH (e:CloudTrailEvent)<-[:RESOURCE]-(:SpaceliftAccount{id: $account_id})
        WHERE e.lastupdated = $update_tag
        MATCH (e)-[r:AFFECTED]->(:EC2Instance)
        RETURN count(r) as count
        """,
        account_id=TEST_SPACELIFT_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )
    affected_count = result.single()["count"]
    assert (
        affected_count == 4
    ), f"Expected 4 AFFECTED relationships, got {affected_count}"

    # Verify instance_ids are stored as lists on the events
    run1_event1 = [e for e in events if e["id"] == "event-uuid-1"][0]
    assert run1_event1["instance_ids"] == ["i-01234567"]


@patch("cartography.intel.spacelift.account.get_account")
@patch("cartography.intel.spacelift.ec2_ownership.get_ec2_ownership")
@patch("cartography.intel.spacelift.runs.get_runs")
@patch("cartography.intel.spacelift.runs.get_entities")
def test_ec2_ownership_cleanup(
    mock_get_entities,
    mock_get_runs,
    mock_get_cloudtrail,
    mock_get_account,
    neo4j_session,
):
    """
    Test that cleanup removes stale CloudTrailEvent nodes and relationships.
    """
    # Arrange
    mock_get_account.return_value = TEST_SPACELIFT_ACCOUNT_ID
    mock_get_cloudtrail.return_value = CLOUDTRAIL_EC2_OWNERSHIP_DATA
    mock_get_entities.return_value = []

    _setup_test_infrastructure(neo4j_session)
    _setup_spacelift_runs(neo4j_session, mock_get_runs, mock_get_entities)

    aws_session = MagicMock()
    sync_ec2_ownership(
        neo4j_session,
        aws_session,
        TEST_S3_BUCKET,
        TEST_S3_PREFIX,
        TEST_UPDATE_TAG,
        TEST_SPACELIFT_ACCOUNT_ID,
    )

    # Verify initial state
    result = neo4j_session.run(
        """
        MATCH (e:CloudTrailEvent)<-[:RESOURCE]-(a:SpaceliftAccount{id: $account_id})
        WHERE e.lastupdated = $update_tag
        RETURN count(e) as count
        """,
        account_id=TEST_SPACELIFT_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )
    initial_count = result.single()["count"]
    assert initial_count == 4

    # Act: Second sync with only one event (simulating stale data)
    new_update_tag = TEST_UPDATE_TAG + 1
    mock_get_cloudtrail.return_value = [
        CLOUDTRAIL_EC2_OWNERSHIP_DATA[0]
    ]  # Only first event

    sync_ec2_ownership(
        neo4j_session,
        aws_session,
        TEST_S3_BUCKET,
        TEST_S3_PREFIX,
        new_update_tag,
        TEST_SPACELIFT_ACCOUNT_ID,
    )

    # Assert: Verify that stale events were cleaned up
    result = neo4j_session.run(
        """
        MATCH (e:CloudTrailEvent)<-[:RESOURCE]-(a:SpaceliftAccount{id: $account_id})
        WHERE e.lastupdated = $new_update_tag
        RETURN count(e) as count
        """,
        account_id=TEST_SPACELIFT_ACCOUNT_ID,
        new_update_tag=new_update_tag,
    )
    final_count = result.single()["count"]
    assert (
        final_count == 1
    ), f"Expected 1 CloudTrailEvent after cleanup, got {final_count}"

    # Verify that the remaining event is the correct one (event-uuid-1)
    result = neo4j_session.run(
        """
        MATCH (e:CloudTrailEvent)<-[:RESOURCE]-(a:SpaceliftAccount{id: $account_id})
        WHERE e.lastupdated = $new_update_tag
        RETURN e.id as id, e.event_time as event_time, e.event_name as event_name
        """,
        account_id=TEST_SPACELIFT_ACCOUNT_ID,
        new_update_tag=new_update_tag,
    )
    remaining_event = result.single()
    assert remaining_event["id"] == "event-uuid-1"
    assert remaining_event["event_time"] == "2024-01-01T10:00:00Z"
    assert remaining_event["event_name"] == "DescribeInstances"
