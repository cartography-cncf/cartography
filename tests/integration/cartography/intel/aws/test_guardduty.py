from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.guardduty
from cartography.intel.aws.guardduty import sync
from tests.data.aws.guardduty import GET_FINDINGS
from tests.data.aws.guardduty import LIST_DETECTORS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "123456789012"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.guardduty,
    "get_detectors",
    return_value=LIST_DETECTORS["DetectorIds"],
)
@patch.object(
    cartography.intel.aws.guardduty,
    "get_findings",
    return_value=GET_FINDINGS["Findings"],
)
def test_sync_guardduty_findings(mock_get_findings, mock_get_detectors, neo4j_session):
    """
    Test that GuardDuty findings are correctly synced to the graph and create proper relationships.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Create test EC2 instance and S3 bucket that match the findings
    neo4j_session.run(
        """
        MERGE (instance:EC2Instance {id: $instance_id})
        ON CREATE SET instance.firstseen = timestamp()
        SET instance.lastupdated = $update_tag
        """,
        instance_id="i-99999999",
        update_tag=TEST_UPDATE_TAG,
    )

    neo4j_session.run(
        """
        MERGE (bucket:S3Bucket {id: $bucket_name})
        ON CREATE SET bucket.firstseen = timestamp()
        SET bucket.lastupdated = $update_tag
        """,
        bucket_name="test-bucket",
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert - Check that GuardDuty findings were created
    assert check_nodes(neo4j_session, "GuardDutyFinding", ["id"]) == {
        ("74b1234567890abcdef1234567890abcdef",),
        ("85c2345678901bcdef2345678901bcdef0",),
        ("96d3456789012cdef3456789012cdef01",),
    }

    # Assert - Check that GuardDuty findings have the correct properties
    assert check_nodes(
        neo4j_session, "GuardDutyFinding", ["id", "severity", "resource_type"]
    ) == {
        ("74b1234567890abcdef1234567890abcdef", 8.0, "Instance"),
        ("85c2345678901bcdef2345678901bcdef0", 5.0, "S3Bucket"),
        ("96d3456789012cdef3456789012cdef01", 7.5, "AccessKey"),
    }

    # Assert - Check that GuardDuty findings are connected to the AWSAccount
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "GuardDutyFinding",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "74b1234567890abcdef1234567890abcdef"),
        (TEST_ACCOUNT_ID, "85c2345678901bcdef2345678901bcdef0"),
        (TEST_ACCOUNT_ID, "96d3456789012cdef3456789012cdef01"),
    }

    # Assert - Check that GuardDuty findings have the Risk label
    assert check_nodes(neo4j_session, "Risk", ["id"]) == {
        ("74b1234567890abcdef1234567890abcdef",),
        ("85c2345678901bcdef2345678901bcdef0",),
        ("96d3456789012cdef3456789012cdef01",),
    }

    # Assert - Check that GuardDuty finding is connected to the EC2 instance
    assert check_rels(
        neo4j_session,
        "GuardDutyFinding",
        "id",
        "EC2Instance",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        ("74b1234567890abcdef1234567890abcdef", "i-99999999"),
    }

    # Assert - Check that GuardDuty finding is connected to the S3 bucket
    assert check_rels(
        neo4j_session,
        "GuardDutyFinding",
        "id",
        "S3Bucket",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {
        ("85c2345678901bcdef2345678901bcdef0", "test-bucket"),
    }
