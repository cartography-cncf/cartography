from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.apigatewayv2
from tests.data.aws.apigatewayv2 import GET_APIS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.apigatewayv2,
    "get_apigatewayv2_apis",
    return_value=GET_APIS,
)
def test_sync_apigatewayv2_apis(mock_get_apis, neo4j_session) -> None:
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    cartography.intel.aws.apigatewayv2.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(neo4j_session, "APIGatewayV2API", ["id"]) == {
        ("api-001",),
        ("api-002",),
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "APIGatewayV2API",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "api-001"),
        (TEST_ACCOUNT_ID, "api-002"),
    }
