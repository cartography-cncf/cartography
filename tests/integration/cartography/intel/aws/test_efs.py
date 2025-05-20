from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.efs
from cartography.intel.aws.efs import sync
from tests.data.aws.efs import GET_EFS_MOUNT_TARGETS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-west-2"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.efs,
    "get_efs_mount_targets",
    return_value=GET_EFS_MOUNT_TARGETS,
)
def test_sync_efs(mock_get_mount_targets, neo4j_session):
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
    assert check_nodes(neo4j_session, "EfsMountTarget", ["arn"]) == {
        ("fsmt-9f8e7d6c5b4a3z2x",),
        ("fsmt-abcdef1234567890",),
    }

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "EfsMountTarget",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "fsmt-9f8e7d6c5b4a3z2x",
        ),
        (
            TEST_ACCOUNT_ID,
            "fsmt-abcdef1234567890",
        ),
    }
