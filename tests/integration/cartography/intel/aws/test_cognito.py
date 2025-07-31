from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.cognito
from cartography.intel.aws.cognito import sync
from tests.data.aws.cognito import GET_POOLS
from tests.data.aws.cognito import GET_COGNITO_IDENTITY_POOLS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.cognito,
    "get_identity_pool_roles",
    return_value=GET_COGNITO_IDENTITY_POOLS,
)
@patch.object(
    cartography.intel.aws.cognito,
    "get_identity_pools",
    return_value=GET_POOLS,
)
def test_sync_cognito(mock_get_pools, mock_get_pool_roles, neo4j_session):
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
    assert check_nodes(neo4j_session, "CognitoIdentityPool", ["arn"]) == {
        ("us-east-1:abcd1234-5678-90ef-ghij-klmnopqrstuv",)
    }

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "CognitoIdentityPool",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "us-east-1:abcd1234-5678-90ef-ghij-klmnopqrstuv",
        ),
    }
