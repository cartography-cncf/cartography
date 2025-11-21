from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.snapshots
import cartography.intel.aws.ec2.volumes
import tests.data.aws.ec2.snapshots
import tests.data.aws.ec2.volumes
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


def test_get_snapshots_in_use(neo4j_session):
    # Arrange
    data = tests.data.aws.ec2.volumes.DESCRIBE_VOLUMES
    transformed_data = cartography.intel.aws.ec2.volumes.transform_volumes(
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
    )

    # Act
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )
    cartography.intel.aws.ec2.volumes.load_volumes(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected_snapshots = {
        "sn-01",
        "sn-02",
    }

    actual_snapshots = cartography.intel.aws.ec2.snapshots.get_snapshots_in_use(
        neo4j_session,
        TEST_REGION,
        TEST_ACCOUNT_ID,
    )

    assert expected_snapshots == set(actual_snapshots)


def test_load_snapshots(neo4j_session):
    data = tests.data.aws.ec2.snapshots.DESCRIBE_SNAPSHOTS
    transformed = cartography.intel.aws.ec2.snapshots.transform_snapshots(data)
    cartography.intel.aws.ec2.snapshots.load_snapshots(
        neo4j_session,
        transformed,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "sn-01",
        "sn-02",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:EBSSnapshot) RETURN r.id;
        """,
    )
    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_snapshots_relationships(neo4j_session):
    # Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    # Load Test Volumes
    data = tests.data.aws.ec2.snapshots.DESCRIBE_SNAPSHOTS
    transformed = cartography.intel.aws.ec2.snapshots.transform_snapshots(data)
    cartography.intel.aws.ec2.snapshots.load_snapshots(
        neo4j_session,
        transformed,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected = {
        (TEST_ACCOUNT_ID, "sn-01"),
        (TEST_ACCOUNT_ID, "sn-02"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AWSAccount)-[:RESOURCE]->(n2:EBSSnapshot) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected


@patch.object(
    cartography.intel.aws.ec2.snapshots,
    "get_snapshots",
    return_value=tests.data.aws.ec2.snapshots.DESCRIBE_SNAPSHOTS,
)
@patch.object(
    cartography.intel.aws.ec2.snapshots,
    "get_snapshots_in_use",
    return_value=[],
)
def test_sync_ebs_snapshots(
    mock_get_snapshots_in_use, mock_get_snapshots, neo4j_session
):
    """
    Test that sync_ebs_snapshots correctly loads snapshots and creates proper relationships
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.aws.ec2.snapshots.sync_ebs_snapshots(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert EBSSnapshot nodes exist with expected properties
    expected_snapshot_nodes = {
        ("sn-01", "Snapshot for testing", True, "completed", "vol-0df", 123),
        ("sn-02", "Snapshot for testing", True, "completed", "vol-03", 123),
    }
    assert (
        check_nodes(
            neo4j_session,
            "EBSSnapshot",
            ["id", "description", "encrypted", "state", "volumeid", "volumesize"],
        )
        == expected_snapshot_nodes
    )

    # Assert snapshots are connected to AWS account
    expected_account_relationships = {
        (TEST_ACCOUNT_ID, "sn-01"),
        (TEST_ACCOUNT_ID, "sn-02"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AWSAccount",
            "id",
            "EBSSnapshot",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_account_relationships
    )

    # Assert snapshots have correct region property
    result = neo4j_session.run(
        """
        MATCH (s:EBSSnapshot) RETURN s.id, s.region
        """,
    )
    actual_regions = {(r["s.id"], r["s.region"]) for r in result}
    expected_regions = {
        ("sn-01", TEST_REGION),
        ("sn-02", TEST_REGION),
    }
    assert actual_regions == expected_regions

    # Assert snapshots have correct lastupdated property
    result = neo4j_session.run(
        """
        MATCH (s:EBSSnapshot) RETURN s.id, s.lastupdated
        """,
    )
    actual_update_tags = {(r["s.id"], r["s.lastupdated"]) for r in result}
    expected_update_tags = {
        ("sn-01", TEST_UPDATE_TAG),
        ("sn-02", TEST_UPDATE_TAG),
    }
    assert actual_update_tags == expected_update_tags

    # Assert that the mock was called with expected parameters
    mock_get_snapshots.assert_called_once_with(
        boto3_session,
        TEST_REGION,
        [],  # Empty list since get_snapshots_in_use is mocked to return empty list
    )
    # Note: CREATED_FROM relationships are not created in this test because volumes are not loaded
    # The relationships would be created if volumes existed in the graph


@patch.object(
    cartography.intel.aws.ec2.snapshots,
    "get_snapshots",
    return_value=tests.data.aws.ec2.snapshots.DESCRIBE_SNAPSHOTS,
)
def test_sync_ebs_snapshots_with_snapshots_in_use(mock_get_snapshots, neo4j_session):
    """
    Test that sync_ebs_snapshots correctly handles snapshots that are in use
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Load test volumes that reference snapshots
    volume_data = tests.data.aws.ec2.volumes.DESCRIBE_VOLUMES
    transformed_volume_data = cartography.intel.aws.ec2.volumes.transform_volumes(
        volume_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
    )
    cartography.intel.aws.ec2.volumes.load_volumes(
        neo4j_session,
        transformed_volume_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.aws.ec2.snapshots.sync_ebs_snapshots(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert EBSSnapshot nodes exist with expected properties
    expected_snapshot_nodes = {
        ("sn-01", "Snapshot for testing", True, "completed", "vol-0df", 123),
        ("sn-02", "Snapshot for testing", True, "completed", "vol-03", 123),
    }
    assert (
        check_nodes(
            neo4j_session,
            "EBSSnapshot",
            ["id", "description", "encrypted", "state", "volumeid", "volumesize"],
        )
        == expected_snapshot_nodes
    )

    # Assert snapshots are connected to AWS account
    expected_account_relationships = {
        (TEST_ACCOUNT_ID, "sn-01"),
        (TEST_ACCOUNT_ID, "sn-02"),
    }
    assert (
        check_rels(
            neo4j_session,
            "AWSAccount",
            "id",
            "EBSSnapshot",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_account_relationships
    )

    # Assert snapshots are connected to volumes via CREATED_FROM relationship
    expected_created_from_relationships = {
        ("sn-01", "vol-0df"),
        ("sn-02", "vol-03"),
    }
    assert (
        check_rels(
            neo4j_session,
            "EBSSnapshot",
            "id",
            "EBSVolume",
            "id",
            "CREATED_FROM",
            rel_direction_right=True,
        )
        == expected_created_from_relationships
    )
