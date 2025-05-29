from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.sns
from cartography.intel.aws.sns import sync
from tests.data.aws.sns import GET_SUBSCRIPTION_ATTRIBUTES
from tests.data.aws.sns import GET_TOPIC_ATTRIBUTES
from tests.data.aws.sns import LIST_SUBSCRIPTIONS
from tests.data.aws.sns import LIST_TOPICS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.sns, "get_sns_topics", return_value=LIST_TOPICS["Topics"]
)
@patch.object(
    cartography.intel.aws.sns, "get_topic_attributes", return_value=GET_TOPIC_ATTRIBUTES
)
@patch.object(
    cartography.intel.aws.sns, "get_subscriptions", return_value=LIST_SUBSCRIPTIONS
)
@patch.object(
    cartography.intel.aws.sns,
    "get_subscription_attributes",
    return_value=GET_SUBSCRIPTION_ATTRIBUTES,
)
def test_sync_sns(
    mock_get_subscription_attributes,
    mock_get_subscriptions,
    mock_get_topic_attributes,
    mock_get_sns_topics,
    neo4j_session,
):
    """
    Test that SNS topics and subscriptions are correctly synced to the graph.
    """
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(neo4j_session, "SNSTopic", ["arn"]) == {
        ("arn:aws:sns:us-east-1:123456789012:test-topic",),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "SNSTopic",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "arn:aws:sns:us-east-1:123456789012:test-topic"),
    }

    assert check_nodes(neo4j_session, "SNSTopicSubscription", ["arn"]) == {
        (
            "arn:aws:sns:us-east-1:123456789012:my-topic:1111aaaa-2222-bbbb-3333-cccc4444dddd",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "SNSTopicSubscription",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:sns:us-east-1:123456789012:my-topic:1111aaaa-2222-bbbb-3333-cccc4444dddd",
        ),
    }
