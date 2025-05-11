from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.cloudtrail
from cartography.intel.aws.cloudtrail import sync
from tests.data.aws.cloudtrail import GET_CLOUDTRAIL_TRAIL
from tests.data.aws.cloudtrail import LIST_CLOUDTRAIL_TRAILS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.cloudtrail,
    "get_cloudtrail_trails",
    return_value=LIST_CLOUDTRAIL_TRAILS,
)
@patch.object(
    cartography.intel.aws.cloudtrail,
    "get_cloudtrail_trail",
    return_value=GET_CLOUDTRAIL_TRAIL,
)
def test_sync_cloudtrail(mock_get_vols, mock_get_trails, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "CloudTrailTrail", ["arn"]) == {
        ("arn:aws:cloudtrail:us-east-1:123456789012:trail/test-trail",),
    }

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "CloudTrailTrail",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "arn:aws:cloudtrail:us-east-1:123456789012:trail/test-trail"),
    }
