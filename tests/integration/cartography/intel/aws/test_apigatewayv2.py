from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.apigatewayv2
from tests.data.aws.apigatewayv2 import GET_APIS
from tests.data.aws.apigatewayv2 import STAGES_BY_API_ID
from tests.data.aws.apigatewayv2 import STAGE_API_001_DEV_ARN
from tests.data.aws.apigatewayv2 import STAGE_API_001_PROD_ARN
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789

NO_STAGES = {"api-001": [], "api-002": []}


@patch.object(
    cartography.intel.aws.apigatewayv2,
    "get_apigatewayv2_apis",
    return_value=GET_APIS,
)
@patch.object(
    cartography.intel.aws.apigatewayv2,
    "get_apigatewayv2_stages",
    return_value=STAGES_BY_API_ID,
)
def test_sync_apigatewayv2_apis(
    mock_get_stages,
    mock_get_apis,
    neo4j_session,
) -> None:
    # Arrange
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.aws.apigatewayv2.sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSAPIGatewayV2API", ["id"]) == {
        ("api-001",),
        ("api-002",),
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSAPIGatewayV2API",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "api-001"),
        (TEST_ACCOUNT_ID, "api-002"),
    }
    assert check_nodes(neo4j_session, "AWSAPIGatewayV2Stage", ["id"]) == {
        (STAGE_API_001_PROD_ARN,),
        (STAGE_API_001_DEV_ARN,),
    }
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSAPIGatewayV2Stage",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, STAGE_API_001_PROD_ARN),
        (TEST_ACCOUNT_ID, STAGE_API_001_DEV_ARN),
    }
    assert check_rels(
        neo4j_session,
        "AWSAPIGatewayV2API",
        "id",
        "AWSAPIGatewayV2Stage",
        "id",
        "ASSOCIATED_WITH",
        rel_direction_right=True,
    ) == {
        ("api-001", STAGE_API_001_PROD_ARN),
        ("api-001", STAGE_API_001_DEV_ARN),
    }


@patch.object(
    cartography.intel.aws.apigatewayv2,
    "get_apigatewayv2_apis",
    return_value=GET_APIS,
)
@patch.object(
    cartography.intel.aws.apigatewayv2,
    "get_apigatewayv2_stages",
    return_value=STAGES_BY_API_ID,
)
def test_sync_removes_stages_deleted_from_aws(
    mock_get_stages,
    mock_get_apis,
    neo4j_session,
) -> None:
    # Arrange
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    cartography.intel.aws.apigatewayv2.sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )
    # The next sync sees the APIs without any stages.
    mock_get_stages.return_value = NO_STAGES

    # Act
    cartography.intel.aws.apigatewayv2.sync(
        neo4j_session,
        MagicMock(),
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG + 1,
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSAPIGatewayV2Stage", ["id"]) == set()
    assert check_nodes(neo4j_session, "AWSAPIGatewayV2API", ["id"]) == {
        ("api-001",),
        ("api-002",),
    }
