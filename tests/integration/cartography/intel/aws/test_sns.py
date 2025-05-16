from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.sns
from cartography.intel.aws.sns import sync
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789

TEST_TOPIC_DATA = [{
    'TopicArn': 'arn:aws:sns:us-east-1:123456789012:test-topic',
    'TopicName': 'test-topic',
    'DisplayName': 'Test Topic',
    'Owner': '123456789012',
    'SubscriptionsPending': 0,
    'SubscriptionsConfirmed': 1,
    'SubscriptionsDeleted': 0,
    'DeliveryPolicy': '',
    'EffectiveDeliveryPolicy': '',
    'KmsMasterKeyId': '',
    'Region': 'us-east-1',
}]

@patch.object(
    cartography.intel.aws.sns,
    "transform_sns_topics",
    return_value=TEST_TOPIC_DATA
)
def test_sync_sns(mock_transform, neo4j_session):
    """
    Test that SNS topics are correctly synced to the graph.
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