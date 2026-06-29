from unittest.mock import MagicMock
from unittest.mock import patch

import botocore.exceptions

import cartography.intel.aws.inspector
from cartography.intel.aws.inspector import _sync_findings_for_account
from cartography.intel.aws.inspector import BATCH_SIZE
from cartography.intel.aws.inspector import sync
from tests.data.aws.inspector import LIST_FINDINGS_EC2_PACKAGE
from tests.data.aws.inspector import LIST_FINDINGS_NETWORK
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456
TEST_REGION = "us-west-2"
TEST_ACC_ID_1 = "123456789011"
TEST_ACC_ID_2 = "123456789012"


@patch.object(
    cartography.intel.aws.inspector,
    "get_inspector_findings",
    return_value=[LIST_FINDINGS_NETWORK],
)
def test_sync_inspector_network_findings(mock_get, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    # Add some fake accounts
    neo4j_session.run(
        """
        MERGE (:AWSAccount{id: '123456789012'})
        MERGE (:AWSAccount{id: '123456789011'})
        """,
    )
    # Add some fake instances
    neo4j_session.run(
        """
        MERGE (:EC2Instance{id: 'i-instanceid', instanceid: 'i-instanceid'})
        """,
    )

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACC_ID_1,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACC_ID_1},
    )

    # Assert Finding to EC2Instance exists
    assert check_rels(
        neo4j_session,
        "AWSInspectorFinding",
        "id",
        "EC2Instance",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        ("arn:aws:test123", "i-instanceid"),
    }

    # Assert AWSAccount to Finding exists
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSInspectorFinding",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("123456789011", "arn:aws:test123"),
    }


@patch.object(
    cartography.intel.aws.inspector,
    "get_inspector_findings",
    return_value=[LIST_FINDINGS_EC2_PACKAGE],
)
def test_sync_inspector_ec2_package_findings(mock_get, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    # Remove everything previously put in the test graph since the fixture scope is set to module and not function.
    neo4j_session.run(
        """
        MATCH (n) DETACH DELETE n;
        """,
    )
    # Add some fake accounts
    neo4j_session.run(
        """
        MERGE (:AWSAccount{id: '123456789012'})
        MERGE (:AWSAccount{id: '123456789011'})
        """,
    )
    # Add some fake instances
    neo4j_session.run(
        """
        MERGE (:EC2Instance{id: 'i-88503981029833100', instanceid: 'i-88503981029833100'})
        MERGE (:EC2Instance{id: 'i-88503981029833101', instanceid: 'i-88503981029833101'})
        """,
    )

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACC_ID_2,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACC_ID_2},
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSInspectorFinding",
        "id",
        "EC2Instance",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        ("arn:aws:test456", "i-88503981029833100"),
        ("arn:aws:test789", "i-88503981029833101"),
    }

    assert check_rels(
        neo4j_session,
        "AWSInspectorFinding",
        "id",
        "AWSInspectorPackage",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {
        ("arn:aws:test456", "kernel-tools|0:4.9.17-6.29.amzn1.X86_64"),
        ("arn:aws:test456", "kernel|0:4.9.17-6.29.amzn1.X86_64"),
        ("arn:aws:test789", "openssl|0:1.0.2k-1.amzn2.X86_64"),
    }

    # Assert AWSAccount RESOURCE to Finding exists
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSInspectorFinding",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("123456789012", "arn:aws:test456"),
        ("123456789012", "arn:aws:test789"),
    }

    # Assert AWSAccount MEMBER to Finding exists
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSInspectorFinding",
        "id",
        "MEMBER",
        rel_direction_right=True,
    ) == {
        ("123456789011", "arn:aws:test789"),
        ("123456789012", "arn:aws:test456"),
    }

    # Assert AWSAccount RESOURCE to Package exists
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSInspectorPackage",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("123456789012", "kernel-tools|0:4.9.17-6.29.amzn1.X86_64"),
        ("123456789012", "kernel|0:4.9.17-6.29.amzn1.X86_64"),
        ("123456789012", "openssl|0:1.0.2k-1.amzn2.X86_64"),
    }


@patch.object(
    cartography.intel.aws.inspector,
    "get_inspector_findings",
    side_effect=botocore.exceptions.ClientError(
        error_response={"Error": {"Code": "ValidationException", "Message": ""}},
        operation_name="ListFindings",
    ),
)
def test_sync_findings_for_account_skips_validation_exception(
    mock_get,
    neo4j_session,
):
    boto3_session = MagicMock()
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run("MERGE (:AWSAccount{id: $id})", id=TEST_ACC_ID_1)

    _sync_findings_for_account(
        neo4j_session,
        boto3_session,
        TEST_REGION,
        TEST_ACC_ID_1,
        TEST_UPDATE_TAG,
        TEST_ACC_ID_1,
    )

    mock_get.assert_called_once_with(
        boto3_session,
        TEST_REGION,
        TEST_ACC_ID_1,
        BATCH_SIZE,
    )
    assert check_nodes(neo4j_session, "AWSInspectorFinding", ["id"]) == set()


def _raising_findings_generator(*args, **kwargs):
    # Mimics get_inspector_findings raising a connection-level error while the
    # paginator is being iterated (the failure mode reported for unreachable /
    # opt-in inspector2 regional endpoints).
    raise botocore.exceptions.ConnectTimeoutError(
        endpoint_url="https://inspector2.me-south-1.amazonaws.com/findings/list",
    )
    yield  # pragma: no cover - makes this function a generator


@patch.object(
    cartography.intel.aws.inspector,
    "get_member_accounts",
    return_value=[],
)
@patch.object(
    cartography.intel.aws.inspector,
    "get_inspector_findings",
    side_effect=_raising_findings_generator,
)
def test_sync_inspector_survives_connection_timeout(
    mock_get,
    mock_members,
    neo4j_session,
):
    # Arrange: a finding from a previous (successful) run already lives in the
    # graph, stamped with an older update tag.
    old_update_tag = TEST_UPDATE_TAG - 1
    boto3_session = MagicMock()
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (a:AWSAccount{id: $acc})
        MERGE (f:AWSInspectorFinding{id: 'arn:aws:stale'})
        SET f.lastupdated = $old_tag
        MERGE (a)-[r:RESOURCE]->(f)
        SET r.lastupdated = $old_tag
        """,
        acc=TEST_ACC_ID_1,
        old_tag=old_update_tag,
    )

    # Act: a fresh sync hits a transient connection failure for the region.
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACC_ID_1,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACC_ID_1},
    )

    # Assert: the account sync completed without raising, and cleanup was skipped
    # so the last-known-good finding from the previous run was preserved.
    assert check_nodes(neo4j_session, "AWSInspectorFinding", ["id"]) == {
        ("arn:aws:stale",),
    }


@patch.object(
    cartography.intel.aws.inspector,
    "get_inspector_findings",
    return_value=[],
)
@patch.object(cartography.intel.aws.inspector, "create_boto3_client")
@patch.object(
    cartography.intel.aws.inspector,
    "aws_paginate",
    side_effect=botocore.exceptions.ConnectTimeoutError(
        endpoint_url="https://inspector2.me-south-1.amazonaws.com/members/list",
    ),
)
def test_sync_inspector_preserves_data_on_member_listing_timeout(
    mock_paginate,
    mock_client,
    mock_findings,
    neo4j_session,
):
    # This exercises the real get_member_accounts() decorator stack: a transient
    # connection failure while listing members must NOT be swallowed into an empty
    # member list (which would let cleanup run and delete stale member findings).
    old_update_tag = TEST_UPDATE_TAG - 1
    boto3_session = MagicMock()
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    # A delegated-member finding from a previous successful run, stamped older.
    neo4j_session.run(
        """
        MERGE (a:AWSAccount{id: $acc})
        MERGE (f:AWSInspectorFinding{id: 'arn:aws:stale-member'})
        SET f.lastupdated = $old_tag
        MERGE (a)-[r:RESOURCE]->(f)
        SET r.lastupdated = $old_tag
        """,
        acc=TEST_ACC_ID_1,
        old_tag=old_update_tag,
    )

    # Act: list_members connect-times-out for the region.
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACC_ID_1,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACC_ID_1},
    )

    # Assert: the region was skipped, cleanup was skipped, and the stale member
    # finding was preserved rather than deleted.
    assert check_nodes(neo4j_session, "AWSInspectorFinding", ["id"]) == {
        ("arn:aws:stale-member",),
    }
