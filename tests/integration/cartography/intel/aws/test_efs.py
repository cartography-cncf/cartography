from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.efs
from cartography.intel.aws.efs import sync
from tests.data.aws.efs import GET_EFS_ACCESS_POINTS
from tests.data.aws.efs import GET_EFS_FILE_SYSTEMS
from tests.data.aws.efs import GET_EFS_MOUNT_TARGETS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-west-2"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.efs,
    "get_efs_access_points",
    return_value=GET_EFS_ACCESS_POINTS,
)
@patch.object(
    cartography.intel.aws.efs,
    "get_efs_mount_targets",
    return_value=GET_EFS_MOUNT_TARGETS,
)
@patch.object(
    cartography.intel.aws.efs,
    "get_efs_file_systems",
    return_value=GET_EFS_FILE_SYSTEMS,
)
def test_sync_efs(
    mock_get_efs_access_points,
    mock_get_file_systems,
    mock_get_mount_targets,
    neo4j_session,
):
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

    assert check_nodes(neo4j_session, "EfsFileSystem", ["arn"]) == {
        ("arn:aws:elasticfilesystem:us-west-2:123456789012:file-system/fs-abc12345",),
        ("arn:aws:elasticfilesystem:us-west-2:123456789012:file-system/fs-def67890",),
    }

    assert check_nodes(neo4j_session, "EfsAccessPoint", ["arn"]) == {
        (
            "arn:aws:elasticfilesystem:us-west-2:123456789012:access-point/fsap-111aaa222bbb333cc",
        ),
        (
            "arn:aws:elasticfilesystem:us-west-2:123456789012:access-point/fsap-444ddd555eee666ff",
        ),
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

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "EfsFileSystem",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:elasticfilesystem:us-west-2:123456789012:file-system/fs-abc12345",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:elasticfilesystem:us-west-2:123456789012:file-system/fs-def67890",
        ),
    }

    assert check_rels(
        neo4j_session,
        "EfsMountTarget",
        "arn",
        "EfsFileSystem",
        "arn",
        "ATTACHED_TO",
        rel_direction_right=True,
    ) == {
        (
            "fsmt-9f8e7d6c5b4a3z2x",
            "arn:aws:elasticfilesystem:us-west-2:123456789012:file-system/fs-abc12345",
        ),
        (
            "fsmt-abcdef1234567890",
            "arn:aws:elasticfilesystem:us-west-2:123456789012:file-system/fs-def67890",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "EfsAccessPoint",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:elasticfilesystem:us-west-2:123456789012:access-point/fsap-111aaa222bbb333cc",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:elasticfilesystem:us-west-2:123456789012:access-point/fsap-444ddd555eee666ff",
        ),
    }

    assert check_rels(
        neo4j_session,
        "EfsAccessPoint",
        "arn",
        "EfsFileSystem",
        "id",
        "ACCESS_POINT_OF",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:elasticfilesystem:us-west-2:123456789012:access-point/fsap-111aaa222bbb333cc",
            "fs-abc12345",
        ),
        (
            "arn:aws:elasticfilesystem:us-west-2:123456789012:access-point/fsap-444ddd555eee666ff",
            "fs-def67890",
        ),
    }
