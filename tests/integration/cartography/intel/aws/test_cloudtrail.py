from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.cloudtrail
import cartography.intel.aws.cloudwatch
from cartography.intel.aws.cloudtrail import sync
from tests.data.aws.cloudtrail import BUCKETS
from tests.data.aws.cloudtrail import DESCRIBE_CLOUDTRAIL_TRAILS
from tests.data.aws.cloudwatch import GET_CLOUDWATCH_LOG_GROUPS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_buckets(neo4j_session):
    cartography.intel.aws.s3.load_s3_buckets(
        neo4j_session,
        BUCKETS,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


def _ensure_local_neo4j_has_test_cloudwatch_log_groups(neo4j_session):
    cartography.intel.aws.cloudwatch.load_cloudwatch_log_groups(
        neo4j_session,
        GET_CLOUDWATCH_LOG_GROUPS,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.aws.cloudtrail,
    "get_cloudtrail_trails",
    return_value=DESCRIBE_CLOUDTRAIL_TRAILS,
)
def test_sync_cloudtrail(mock_get_trails, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _ensure_local_neo4j_has_test_buckets(neo4j_session)
    _ensure_local_neo4j_has_test_cloudwatch_log_groups(neo4j_session)

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

    assert check_rels(
        neo4j_session,
        "CloudTrailTrail",
        "arn",
        "S3Bucket",
        "name",
        "LOGS_TO",
        rel_direction_right=True,
    ) == {
        ("arn:aws:cloudtrail:us-east-1:123456789012:trail/test-trail", "test-bucket"),
    }

    assert check_rels(
        neo4j_session,
        "CloudTrailTrail",
        "id",
        "CloudWatchLogGroup",
        "id",
        "SENDS_LOGS_TO_CLOUDWATCH",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:cloudtrail:us-east-1:123456789012:trail/test-trail",
            "arn:aws:logs:eu-west-1:123456789012:log-group:/aws/lambda/process-orders",
        ),
    }
