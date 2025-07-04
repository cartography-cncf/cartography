from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.guardduty
from cartography.intel.aws.guardduty import sync
from tests.data.aws.guardduty import FINDINGS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456
TEST_REGION = "us-east-1"
TEST_ACCOUNT_ID = "111111111111"
DETECTOR_ID = "det123"


@patch.object(cartography.intel.aws.guardduty, "get_detectors", return_value=[DETECTOR_ID])
@patch.object(cartography.intel.aws.guardduty, "get_guardduty_findings", return_value=FINDINGS)
def test_sync_guardduty(mock_get_findings, mock_get_detectors, neo4j_session):
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    neo4j_session.run("MERGE (:EC2Instance {id: 'i-abc123'})")
    neo4j_session.run("MERGE (:S3Bucket {id: 'my-bucket'})")

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(neo4j_session, "AWSGuardDutyFinding", ["id", "type"]) == {
        ("finding-1", "Recon:EC2/PortProbeUnprotectedPort"),
        ("finding-2", "Recon:S3/BucketEnumeration"),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSGuardDutyFinding",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {(TEST_ACCOUNT_ID, "finding-1"), (TEST_ACCOUNT_ID, "finding-2")}

    assert check_rels(
        neo4j_session,
        "AWSGuardDutyFinding",
        "id",
        "EC2Instance",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {("finding-1", "i-abc123")}

    assert check_rels(
        neo4j_session,
        "AWSGuardDutyFinding",
        "id",
        "S3Bucket",
        "id",
        "AFFECTS",
        rel_direction_right=True,
    ) == {("finding-2", "my-bucket")}
