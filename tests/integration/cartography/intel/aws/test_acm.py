from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.acm
from cartography.intel.aws.acm import sync
from tests.data.aws import acm as test_data
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789
LISTENER_ARN = (
    "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/test-lb/abcd/efgh"
)


@patch.object(
    cartography.intel.aws.acm,
    "get_acm_certificates",
    return_value=[test_data.DESCRIBE_CERTIFICATE["Certificate"]],
)
def test_sync_acm(mock_get_certs, neo4j_session):
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Pre-create listener node to attach relationship
    neo4j_session.run("MERGE (:ELBV2Listener {id: $id})", id=LISTENER_ARN)

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(neo4j_session, "ACMCertificate", ["arn", "domainname"]) == {
        ("arn:aws:acm:us-east-1:000000000000:certificate/test-cert", "example.com")
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "ACMCertificate",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {(TEST_ACCOUNT_ID, "arn:aws:acm:us-east-1:000000000000:certificate/test-cert")}

    assert check_rels(
        neo4j_session,
        "ACMCertificate",
        "arn",
        "ELBV2Listener",
        "id",
        "USED_BY",
        rel_direction_right=True,
    ) == {("arn:aws:acm:us-east-1:000000000000:certificate/test-cert", LISTENER_ARN)}
