from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.cloudwatch
from cartography.intel.aws.cloudwatch import sync
from tests.data.aws.cloudwatch import GET_CLOUDWATCH_LOG_GROUPS
from tests.data.aws.cloudwatch import GET_CLOUDWATCH_LOG_METRIC_FILTERS
from tests.data.aws.cloudwatch import GET_CLOUDWATCH_METRIC_ALARMS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.cloudwatch,
    "get_cloudwatch_metric_alarms",
    return_value=GET_CLOUDWATCH_METRIC_ALARMS,
)
@patch.object(
    cartography.intel.aws.cloudwatch,
    "get_cloudwatch_log_metric_filters",
    return_value=GET_CLOUDWATCH_LOG_METRIC_FILTERS,
)
@patch.object(
    cartography.intel.aws.cloudwatch,
    "get_cloudwatch_log_groups",
    return_value=GET_CLOUDWATCH_LOG_GROUPS,
)
def test_sync_cloudwatch(
    mock_get_log_groups,
    mock_get_log_metric_filters,
    moct_get_metric_alarms,
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
    assert check_nodes(neo4j_session, "CloudWatchLogGroup", ["arn"]) == {
        ("arn:aws:logs:eu-west-1:123456789012:log-group:/aws/lambda/process-orders",),
        (
            "arn:aws:logs:eu-west-1:123456789012:log-group:/aws/codebuild/sample-project",
        ),
    }

    assert check_nodes(neo4j_session, "CloudWatchLogMetricFilter", ["id"]) == {
        ("/aws/lambda/process-orders:HighErrorRate",),
        ("/aws/codebuild/sample-project:AuthFailures",),
    }

    assert check_nodes(neo4j_session, "CloudWatchMetricAlarm", ["arn"]) == {
        ("arn:aws:cloudwatch:us-east-1:123456789012:alarm:HighErrorCountAlarm",),
        ("arn:aws:cloudwatch:us-east-1:123456789012:alarm:CompositeErrorRateAlarm",),
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
            "arn:aws:logs:eu-west-1:123456789012:log-group:/aws/lambda/process-orders",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:logs:eu-west-1:123456789012:log-group:/aws/codebuild/sample-project",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "CloudWatchLogMetricFilter",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "/aws/lambda/process-orders:HighErrorRate"),
        (TEST_ACCOUNT_ID, "/aws/codebuild/sample-project:AuthFailures"),
    }

    assert check_rels(
        neo4j_session,
        "CloudWatchLogMetricFilter",
        "id",
        "CloudWatchLogGroup",
        "log_group_name",
        "METRIC_FILTER_OF",
        rel_direction_right=True,
    ) == {
        (
            "/aws/lambda/process-orders:HighErrorRate",
            "/aws/lambda/process-orders",
        ),
        (
            "/aws/codebuild/sample-project:AuthFailures",
            "/aws/codebuild/sample-project",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "CloudWatchMetricAlarm",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:cloudwatch:us-east-1:123456789012:alarm:HighErrorCountAlarm",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:cloudwatch:us-east-1:123456789012:alarm:CompositeErrorRateAlarm",
        ),
    }
