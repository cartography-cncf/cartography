from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.cloudtrail
import cartography.intel.aws.cloudwatch
import cartography.intel.aws.kms
import tests.data.aws.kms
from cartography.intel.aws.cloudtrail import sync
from tests.data.aws.cloudtrail import GET_CLOUDTRAIL_TRAIL
from tests.data.aws.cloudtrail import LIST_CLOUDTRAIL_TRAILS
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


def _ensure_local_neo4j_has_test_cloudwatch_log_groups(neo4j_session):
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    cloudwatch_log_groups_data = GET_CLOUDWATCH_LOG_GROUPS
    cartography.intel.aws.cloudwatch.load_cloudwatch_log_groups(
        neo4j_session,
        cloudwatch_log_groups_data,
        TEST_REGION_FOR_KMS,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


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

    _ensure_local_neo4j_has_test_kms_keys(neo4j_session)
    _ensure_local_neo4j_has_test_cloudwatch_log_groups(neo4j_session)

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
    assert check_nodes(neo4j_session, "CloudTrailTrail", ["arn"]) == {
        ("arn:aws:cloudtrail:eu-west-1:000000000000:trail/test-trail",),
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
        (TEST_ACCOUNT_ID, "arn:aws:cloudtrail:eu-west-1:000000000000:trail/test-trail"),
    }

    assert check_rels(
        neo4j_session,
        "CloudTrailTrail",
        "id",
        "KMSKey",
        "id",
        "ENCRYPTED_BY",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:cloudtrail:eu-west-1:000000000000:trail/test-trail",
            "9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
        )
    }

    assert check_rels(
        neo4j_session,
        "CloudTrailTrail",
        "id",
        "CloudWatchLogGroup",
        "id",
        "SEND_LOGS_TO",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:cloudtrail:eu-west-1:000000000000:trail/test-trail",
            "arn:aws:logs:eu-west-1:000000000000:log-group:/aws/codebuild/sample-project",
        ),
    }
