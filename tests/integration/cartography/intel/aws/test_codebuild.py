from unittest.mock import MagicMock

import cartography.intel.aws.codebuild
from cartography.intel.aws.codebuild import sync
from tests.data.aws.codebuild import GET_PROJECTS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


def test_sync_cloudwatch(mocker, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    boto3_session.get_partition_for_region.return_value = "aws"
    boto3_session.get_available_regions.return_value = [TEST_REGION]
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    mocker.patch.object(
        cartography.intel.aws.codebuild,
        "get_all_codebuild_projects",
        return_value=GET_PROJECTS,
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

    # Assert
    assert check_nodes(neo4j_session, "CodeBuildProject", ["arn"]) == {
        ("arn:aws:codebuild:eu-west-1:123456789012:project/frontend-build",),
        ("arn:aws:codebuild:eu-west-1:123456789012:project/backend-deploy",),
    }

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "CodeBuildProject",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:codebuild:eu-west-1:123456789012:project/frontend-build",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:codebuild:eu-west-1:123456789012:project/backend-deploy",
        ),
    }
