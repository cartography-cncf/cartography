from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.cloudwatch
import cartography.intel.aws.kms
import tests.data.aws.kms
from cartography.intel.aws.cloudwatch import sync
from tests.data.aws.cloudwatch import GET_CLOUDWATCH_LOG_GROUPS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_REGION_FOR_KMS = "eu-west-1"
TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_kms_keys(neo4j_session):
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    kms_keys_data = tests.data.aws.kms.DESCRIBE_KEYS
    cartography.intel.aws.kms.load_kms_keys(
        neo4j_session,
        kms_keys_data,
        TEST_REGION_FOR_KMS,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.aws.cloudwatch,
    "get_cloudwatch_log_groups",
    return_value=GET_CLOUDWATCH_LOG_GROUPS,
)
def test_sync_cloudwatch(mock_get_log_groups, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    _ensure_local_neo4j_has_test_kms_keys(neo4j_session)
    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION_FOR_KMS],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "CloudWatchLogGroup", ["arn"]) == {
        ("arn:aws:logs:eu-west-1:000000000000:log-group:/aws/lambda/process-orders",),
        (
            "arn:aws:logs:eu-west-1:000000000000:log-group:/aws/codebuild/sample-project",
        ),
    }

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "CloudWatchLogGroup",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:logs:eu-west-1:000000000000:log-group:/aws/lambda/process-orders",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:logs:eu-west-1:000000000000:log-group:/aws/codebuild/sample-project",
        ),
    }

    assert check_rels(
        neo4j_session,
        "CloudWatchLogGroup",
        "id",
        "KMSKey",
        "id",
        "ENCRYPTED_BY",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:logs:eu-west-1:000000000000:log-group:/aws/lambda/process-orders",
            "9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        ),
        (
            "arn:aws:logs:eu-west-1:000000000000:log-group:/aws/codebuild/sample-project",
            "9a1ad414-6e3b-47ce-8366-6b8f28bc777g",
        ),
    }
