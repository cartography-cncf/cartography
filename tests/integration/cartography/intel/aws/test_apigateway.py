from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.apigateway
import tests.data.aws.apigateway
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.apigateway,
    "get_rest_api_deployments",
    return_value=tests.data.aws.apigateway.GET_REST_API_DEPLOYMENTS,
)
@patch.object(
    cartography.intel.aws.apigateway,
    "get_apigateway_rest_apis",
    return_value=tests.data.aws.apigateway.GET_REST_APIS,
)
@patch.object(
    cartography.intel.aws.apigateway,
    "get_rest_api_details",
    return_value=tests.data.aws.apigateway.GET_REST_API_DETAILS,
)
def test_sync_apigateway(
    mock_get_details, mock_get_apis, mock_get_deployments, neo4j_session
):
    """
    Verify that API Gateway resources are properly synced
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.aws.apigateway.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert REST APIs exist with correct policy-level access (anonymous_access)
    # and network-level exposure (exposed_internet) based on endpoint type
    assert check_nodes(
        neo4j_session,
        "AWSAPIGatewayRestAPI",
        ["id", "anonymous_access", "endpoint_type", "exposed_internet"],
    ) == {
        # test-001: REGIONAL endpoint (internet exposed) + open policy (anonymous access)
        ("test-001", True, "REGIONAL", True),
        # test-002: PRIVATE endpoint (VPC only) + restricted policy (no anonymous access)
        ("test-002", False, "PRIVATE", False),
    }

    # Assert Stages exist
    assert check_nodes(neo4j_session, "AWSAPIGatewayStage", ["id"]) == {
        ("arn:aws:apigateway:::test-001/Cartography-testing-infra",),
        ("arn:aws:apigateway:::test-002/Cartography-testing-unit",),
    }

    # Assert Certificates exist
    assert check_nodes(neo4j_session, "AWSAPIGatewayClientCertificate", ["id"]) == {
        ("cert-001",),
        ("cert-002",),
    }

    # Assert Resources exist
    assert check_nodes(neo4j_session, "AWSAPIGatewayResource", ["id"]) == {
        ("3kzxbg5sa2",),
    }

    assert check_nodes(neo4j_session, "AWSAPIGatewayDeployment", ["id"]) == {
        ("test-001/dep1",),
        ("test-002/dep2",),
    }

    assert check_nodes(neo4j_session, "AWSAPIGatewayMethod", ["id"]) == {
        ("test-001/3kzxbg5sa2/GET",),
    }

    assert check_nodes(neo4j_session, "AWSAPIGatewayIntegration", ["id"]) == {
        ("test-001/3kzxbg5sa2/GET",),
    }

    # Assert AWS Account to REST API relationships
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSAPIGatewayRestAPI",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "test-001"),
        (TEST_ACCOUNT_ID, "test-002"),
    }

    # Assert AWS Account to Stage relationships
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSAPIGatewayStage",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "arn:aws:apigateway:::test-001/Cartography-testing-infra"),
        (TEST_ACCOUNT_ID, "arn:aws:apigateway:::test-002/Cartography-testing-unit"),
    }

    # Assert AWS Account to Certificate relationships
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSAPIGatewayClientCertificate",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "cert-001"),
        (TEST_ACCOUNT_ID, "cert-002"),
    }
    # Assert AWS Account to Resource relationships
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSAPIGatewayResource",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "3kzxbg5sa2"),
    }

    # Assert REST API to Stage relationships
    assert check_rels(
        neo4j_session,
        "AWSAPIGatewayRestAPI",
        "id",
        "AWSAPIGatewayStage",
        "id",
        "ASSOCIATED_WITH",
        rel_direction_right=True,
    ) == {
        ("test-001", "arn:aws:apigateway:::test-001/Cartography-testing-infra"),
        ("test-002", "arn:aws:apigateway:::test-002/Cartography-testing-unit"),
    }

    # Assert Stage to Certificate relationships
    assert check_rels(
        neo4j_session,
        "AWSAPIGatewayStage",
        "id",
        "AWSAPIGatewayClientCertificate",
        "id",
        "HAS_CERTIFICATE",
        rel_direction_right=True,
    ) == {
        ("arn:aws:apigateway:::test-001/Cartography-testing-infra", "cert-001"),
        ("arn:aws:apigateway:::test-002/Cartography-testing-unit", "cert-002"),
    }

    # Assert REST API to Resource relationships
    assert check_rels(
        neo4j_session,
        "AWSAPIGatewayRestAPI",
        "id",
        "AWSAPIGatewayResource",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("test-001", "3kzxbg5sa2"),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSAPIGatewayDeployment",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "test-001/dep1"),
        (TEST_ACCOUNT_ID, "test-002/dep2"),
    }

    assert check_rels(
        neo4j_session,
        "AWSAPIGatewayRestAPI",
        "id",
        "AWSAPIGatewayDeployment",
        "id",
        "HAS_DEPLOYMENT",
        rel_direction_right=True,
    ) == {
        ("test-001", "test-001/dep1"),
        ("test-002", "test-002/dep2"),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSAPIGatewayMethod",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "test-001/3kzxbg5sa2/GET"),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSAPIGatewayIntegration",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "test-001/3kzxbg5sa2/GET"),
    }

    assert check_rels(
        neo4j_session,
        "AWSAPIGatewayResource",
        "id",
        "AWSAPIGatewayMethod",
        "id",
        "HAS_METHOD",
        rel_direction_right=True,
    ) == {
        ("3kzxbg5sa2", "test-001/3kzxbg5sa2/GET"),
    }

    assert check_rels(
        neo4j_session,
        "AWSAPIGatewayResource",
        "id",
        "AWSAPIGatewayIntegration",
        "id",
        "HAS_INTEGRATION",
        rel_direction_right=True,
    ) == {
        ("3kzxbg5sa2", "test-001/3kzxbg5sa2/GET"),
    }
