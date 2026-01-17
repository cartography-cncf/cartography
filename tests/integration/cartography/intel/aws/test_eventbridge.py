from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.eventbridge
from cartography.intel.aws.eventbridge import sync
from cartography.intel.aws.iam import load_role_data
from cartography.intel.aws.iam import transform_role_trust_policies
from tests.data.aws.eventbridge import GET_EVENTBRIDGE_RULES
from tests.data.aws.eventbridge import GET_EVENTBRIDGE_TARGETS
from tests.data.aws.iam.roles import ROLES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.eventbridge,
    "get_eventbridge_rules",
    return_value=GET_EVENTBRIDGE_RULES,
)
@patch.object(
    cartography.intel.aws.iam, "get_role_list_data", return_value=ROLES["Roles"]
)
@patch.object(
    cartography.intel.aws.eventbridge,
    "get_eventbridge_targets",
    return_value=GET_EVENTBRIDGE_TARGETS,
)
def test_sync_eventbridge(
    mock_get_targets, mock_get_roles, mock_get_rules, neo4j_session
):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    transformed_role_data = transform_role_trust_policies(
        ROLES["Roles"], TEST_ACCOUNT_ID
    )
    load_role_data(
        neo4j_session,
        transformed_role_data.role_data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
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
    assert check_nodes(neo4j_session, "EventBridgeRule", ["arn"]) == {
        ("arn:aws:events:us-east-1:123456789012:rule/UserSignupRule",),
        ("arn:aws:events:us-east-1:123456789012:rule/DailyCleanupRule",),
    }

    assert check_nodes(neo4j_session, "EventBridgeTarget", ["arn"]) == {
        ("arn:aws:lambda:us-east-1:123456789012:function:ProcessSignup",),
        ("arn:aws:sns:us-east-1:123456789012:NotifyAdmin",),
    }

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "EventBridgeRule",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:events:us-east-1:123456789012:rule/UserSignupRule",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:events:us-east-1:123456789012:rule/DailyCleanupRule",
        ),
    }

    assert check_rels(
        neo4j_session,
        "EventBridgeRule",
        "arn",
        "AWSRole",
        "arn",
        "ASSOCIATED_WITH",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:events:us-east-1:123456789012:rule/UserSignupRule",
            "arn:aws:iam::1234:role/cartography-read-only",
        ),
        (
            "arn:aws:events:us-east-1:123456789012:rule/DailyCleanupRule",
            "arn:aws:iam::1234:role/cartography-service",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "EventBridgeTarget",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-east-1:123456789012:function:ProcessSignup",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:sns:us-east-1:123456789012:NotifyAdmin",
        ),
    }

    assert check_rels(
        neo4j_session,
        "EventBridgeTarget",
        "arn",
        "EventBridgeRule",
        "arn",
        "LINKED_TO_RULE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:lambda:us-east-1:123456789012:function:ProcessSignup",
            "arn:aws:events:us-east-1:123456789012:rule/UserSignupRule",
        ),
        (
            "arn:aws:sns:us-east-1:123456789012:NotifyAdmin",
            "arn:aws:events:us-east-1:123456789012:rule/DailyCleanupRule",
        ),
    }
