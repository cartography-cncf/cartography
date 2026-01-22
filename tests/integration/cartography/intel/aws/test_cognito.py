from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.cognito
from cartography.intel.aws.cognito import sync
from cartography.intel.aws.iam import load_role_data
from cartography.intel.aws.iam import transform_role_trust_policies
from tests.data.aws.cognito import GET_COGNITO_IDENTITY_POOLS
from tests.data.aws.cognito import GET_COGNITO_USER_POOLS
from tests.data.aws.cognito import GET_POOLS
from tests.data.aws.iam.roles import ROLES
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
@patch.object(
    cartography.intel.aws.cognito,
    "get_user_pools",
    return_value=GET_COGNITO_USER_POOLS,
)
@patch.object(
    cartography.intel.aws.iam,
    "get_role_list_data",
    return_value=ROLES["Roles"],
)
def test_sync_cognito(
    mock_get_roles,
    mock_get_user_pools,
    mock_get_pools,
    mock_get_pool_roles,
    neo4j_session,
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
    assert check_nodes(neo4j_session, "CognitoIdentityPool", ["arn"]) == {
        ("us-east-1:abcd1234-5678-90ef-ghij-klmnopqrstuv",)
    }

    assert check_nodes(neo4j_session, "CognitoUserPool", ["arn"]) == {
        ("us-east-1_abc123",),
        ("us-west-2_xyz789",),
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

    assert check_rels(
        neo4j_session,
        "CognitoIdentityPool",
        "arn",
        "AWSRole",
        "arn",
        "ASSOCIATED_WITH",
        rel_direction_right=True,
    ) == {
        (
            "us-east-1:abcd1234-5678-90ef-ghij-klmnopqrstuv",
            "arn:aws:iam::1234:role/cartography-read-only",
        ),
        (
            "us-east-1:abcd1234-5678-90ef-ghij-klmnopqrstuv",
            "arn:aws:iam::1234:role/cartography-service",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "CognitoUserPool",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "us-east-1_abc123"),
        (TEST_ACCOUNT_ID, "us-west-2_xyz789"),
    }
