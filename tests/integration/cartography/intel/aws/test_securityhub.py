from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.securityhub
from tests.data.aws.securityhub import GET_HUB
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.securityhub,
    "get_hub",
    return_value=GET_HUB,
)
def test_sync_hub(mock_get_hub, neo4j_session):
    """
    Ensure that sync() creates SecurityHub nodes and links them to the AWS account.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    cartography.intel.aws.securityhub.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(
        neo4j_session,
        "SecurityHub",
        ["id", "subscribed_at", "auto_enable_controls"],
    ) == {
        (
            "arn:aws:securityhub:us-east-1:000000000000:hub/default",
            1606993517,
            True,
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "SecurityHub",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "arn:aws:securityhub:us-east-1:000000000000:hub/default"),
    }
