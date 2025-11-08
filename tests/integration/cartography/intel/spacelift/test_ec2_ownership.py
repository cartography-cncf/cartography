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
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

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

    # Note: CloudTrail test data references properly-formatted instance IDs
    # that match the regex pattern for real EC2 instances. We create these minimal
    # instances directly rather than using the full EC2 sync.
    neo4j_session.run(
        """
        MERGE (i1:EC2Instance{id: 'i-01234567', instanceid: 'i-01234567'})
        ON CREATE SET i1.firstseen = timestamp()
        SET i1.lastupdated = $update_tag

        MERGE (i2:EC2Instance{id: 'i-89abcdef', instanceid: 'i-89abcdef'})
        ON CREATE SET i2.firstseen = timestamp()
        SET i2.lastupdated = $update_tag

        MERGE (i3:EC2Instance{id: 'i-02345678', instanceid: 'i-02345678'})
        ON CREATE SET i3.firstseen = timestamp()
        SET i3.lastupdated = $update_tag

        WITH i1, i2, i3
        MATCH (a:AWSAccount{id: $aws_id})
        MERGE (a)-[r1:RESOURCE]->(i1)
        ON CREATE SET r1.firstseen = timestamp()
        SET r1.lastupdated = $update_tag

        MERGE (a)-[r2:RESOURCE]->(i2)
        ON CREATE SET r2.firstseen = timestamp()
        SET r2.lastupdated = $update_tag

        MERGE (a)-[r3:RESOURCE]->(i3)
        ON CREATE SET r3.firstseen = timestamp()
        SET r3.lastupdated = $update_tag
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
            "spacelift_account_id": TEST_SPACELIFT_ACCOUNT_ID,
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
    are preserved as separate CloudTrailSpaceliftEvent nodes.
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

    # Assert: Verify CloudTrailSpaceliftEvent nodes created with real CloudTrail eventids
    expected_event_nodes = {
        ("45f1164a-cba5-4169-8b09-8066a2634d9b", "run-1"),  # DescribeInstances
        ("a1b2c3d4-e5f6-4a5b-9c8d-1234567890ab", "run-1"),  # RunInstances
        ("f7e8d9c0-b1a2-4d3e-8f9a-fedcba987654", "run-1"),  # DescribeInstances again
        ("9a8b7c6d-5e4f-4321-ba09-876543210fed", "run-2"),  # RunInstances (2 instances)
    }
    actual_event_nodes = check_nodes(
        neo4j_session, "CloudTrailSpaceliftEvent", ["id", "run_id"]
    )
    assert actual_event_nodes is not None
    assert (
        expected_event_nodes == actual_event_nodes
    ), f"Expected {expected_event_nodes}, got {actual_event_nodes}"

    # Assert: Verify FROM_RUN relationships (one per event)
    expected_from_run_rels = {
        ("45f1164a-cba5-4169-8b09-8066a2634d9b", "run-1"),
        ("a1b2c3d4-e5f6-4a5b-9c8d-1234567890ab", "run-1"),
        ("f7e8d9c0-b1a2-4d3e-8f9a-fedcba987654", "run-1"),
        ("9a8b7c6d-5e4f-4321-ba09-876543210fed", "run-2"),
    }
    actual_from_run_rels = check_rels(
        neo4j_session,
        "CloudTrailSpaceliftEvent",
        "id",
        "SpaceliftRun",
        "id",
        "FROM_RUN",
        rel_direction_right=True,
    )
    assert actual_from_run_rels is not None
    assert (
        expected_from_run_rels == actual_from_run_rels
    ), f"Expected {expected_from_run_rels} FROM_RUN rels, got {actual_from_run_rels}"

    # Assert: Verify AFFECTED relationships (tests one-to-many)
    # Event 4 creates TWO relationships (one event -> multiple instances)
    expected_affected_rels = {
        ("45f1164a-cba5-4169-8b09-8066a2634d9b", "i-01234567"),
        ("a1b2c3d4-e5f6-4a5b-9c8d-1234567890ab", "i-01234567"),
        ("f7e8d9c0-b1a2-4d3e-8f9a-fedcba987654", "i-01234567"),
        ("9a8b7c6d-5e4f-4321-ba09-876543210fed", "i-89abcdef"),  # Event 4 -> instance 1
        ("9a8b7c6d-5e4f-4321-ba09-876543210fed", "i-02345678"),  # Event 4 -> instance 2
    }
    actual_affected_rels = check_rels(
        neo4j_session,
        "CloudTrailSpaceliftEvent",
        "id",
        "EC2Instance",
        "instanceid",
        "AFFECTED",
        rel_direction_right=True,
    )
    assert actual_affected_rels is not None
    assert (
        expected_affected_rels == actual_affected_rels
    ), f"Expected {expected_affected_rels} AFFECTED rels, got {actual_affected_rels}"


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
    Test that cleanup removes stale CloudTrailSpaceliftEvent nodes and relationships.
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
        MATCH (e:CloudTrailSpaceliftEvent)<-[:RESOURCE]-(a:SpaceliftAccount{id: $account_id})
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
        MATCH (e:CloudTrailSpaceliftEvent)<-[:RESOURCE]-(a:SpaceliftAccount{id: $account_id})
        WHERE e.lastupdated = $new_update_tag
        RETURN count(e) as count
        """,
        account_id=TEST_SPACELIFT_ACCOUNT_ID,
        new_update_tag=new_update_tag,
    )
    final_count = result.single()["count"]
    assert (
        final_count == 1
    ), f"Expected 1 CloudTrailSpaceliftEvent after cleanup, got {final_count}"

    # Verify that the remaining event is the correct one (first event)
    result = neo4j_session.run(
        """
        MATCH (e:CloudTrailSpaceliftEvent)
        WHERE e.lastupdated = $new_update_tag
        RETURN e.id as id
        """,
        new_update_tag=new_update_tag,
    )
    remaining_events = result.data()
    assert len(remaining_events) == 1
    assert remaining_events[0]["id"] == "45f1164a-cba5-4169-8b09-8066a2634d9b"
