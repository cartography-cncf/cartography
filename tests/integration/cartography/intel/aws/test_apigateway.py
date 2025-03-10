from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.apigateway
import tests.data.aws.apigateway
from cartography.client.core.tx import load
from cartography.models.aws.apigatewaycertificate import APIGatewayClientCertificateSchema
from cartography.models.aws.apigatewayresource import APIGatewayResourceSchema
from cartography.models.aws.apigatewaystage import APIGatewayStageSchema
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-west-1'
TEST_UPDATE_TAG = 123456789


def test_load_apigateway_rest_apis(neo4j_session):
    data = tests.data.aws.apigateway.GET_REST_APIS
    cartography.intel.aws.apigateway.load_apigateway_rest_apis(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "test-001",
        "test-002",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:APIGatewayRestAPI) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_apigateway_rest_apis_relationships(neo4j_session):
    # Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    # Load Test API Gateway REST APIs
    data = tests.data.aws.apigateway.GET_REST_APIS
    cartography.intel.aws.apigateway.load_apigateway_rest_apis(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    expected = {
        (TEST_ACCOUNT_ID, 'test-001'),
        (TEST_ACCOUNT_ID, 'test-002'),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AWSAccount)-[:RESOURCE]->(n2:APIGatewayRestAPI) RETURN n1.id, n2.id;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_apigateway_stages(neo4j_session):
    data = tests.data.aws.apigateway.GET_STAGES
    load(
        neo4j_session,
        APIGatewayStageSchema(),
        data,
        lastupdated=TEST_UPDATE_TAG,
        AWS_ID=TEST_ACCOUNT_ID,
    )

    expected_nodes = {
        "arn:aws:apigateway:::test-001/Cartography-testing-infra",
        "arn:aws:apigateway:::test-002/Cartography-testing-unit",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:APIGatewayStage) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_apigateway_stages_relationships(neo4j_session):
    # Load Test REST API
    data_rest_api = tests.data.aws.apigateway.GET_REST_APIS
    cartography.intel.aws.apigateway.load_apigateway_rest_apis(
        neo4j_session,
        data_rest_api,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Load test API Gateway Stages
    data_stages = tests.data.aws.apigateway.GET_STAGES
    load(
        neo4j_session,
        APIGatewayStageSchema(),
        data_stages,
        lastupdated=TEST_UPDATE_TAG,
        AWS_ID=TEST_ACCOUNT_ID,
    )

    expected = {
        (
            'test-001',
            'arn:aws:apigateway:::test-001/Cartography-testing-infra',
        ),
        (
            'test-002',
            'arn:aws:apigateway:::test-002/Cartography-testing-unit',
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:APIGatewayRestAPI)-[:ASSOCIATED_WITH]->(n2:APIGatewayStage) RETURN n1.id, n2.id;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_apigateway_certificates(neo4j_session):
    data = tests.data.aws.apigateway.GET_CERTIFICATES
    load(
        neo4j_session,
        APIGatewayClientCertificateSchema(),
        data,
        lastupdated=TEST_UPDATE_TAG,
        AWS_ID=TEST_ACCOUNT_ID,
    )

    expected_nodes = {
        "cert-001",
        "cert-002",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:APIGatewayClientCertificate) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_apigateway_certificates_relationships(neo4j_session):
    # Load test API Gateway Stages
    data_stages = tests.data.aws.apigateway.GET_STAGES
    load(
        neo4j_session,
        APIGatewayStageSchema(),
        data_stages,
        lastupdated=TEST_UPDATE_TAG,
        AWS_ID=TEST_ACCOUNT_ID,
    )

    # Load test Client Certificates
    data_certificates = tests.data.aws.apigateway.GET_CERTIFICATES
    load(
        neo4j_session,
        APIGatewayClientCertificateSchema(),
        data_certificates,
        lastupdated=TEST_UPDATE_TAG,
        AWS_ID=TEST_ACCOUNT_ID,
    )

    expected = {
        (
            'arn:aws:apigateway:::test-001/Cartography-testing-infra',
            'cert-001',
        ),
        (
            'arn:aws:apigateway:::test-002/Cartography-testing-unit',
            'cert-002',
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:APIGatewayStage)-[:HAS_CERTIFICATE]->(n2:APIGatewayClientCertificate) RETURN n1.id, n2.id;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


def test_load_apigateway_resources(neo4j_session):
    data = tests.data.aws.apigateway.GET_RESOURCES
    load(
        neo4j_session,
        APIGatewayResourceSchema(),
        data,
        lastupdated=TEST_UPDATE_TAG,
        AWS_ID=TEST_ACCOUNT_ID,
    )

    expected_nodes = {
        "3kzxbg5sa2",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:APIGatewayResource) RETURN r.id;
        """,
    )
    actual_nodes = {n['r.id'] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_apigateway_resources_relationships(neo4j_session):
    # Load Test REST API
    data_rest_api = tests.data.aws.apigateway.GET_REST_APIS
    cartography.intel.aws.apigateway.load_apigateway_rest_apis(
        neo4j_session,
        data_rest_api,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Load test API Gateway Resource resources
    data_resources = tests.data.aws.apigateway.GET_RESOURCES
    load(
        neo4j_session,
        APIGatewayResourceSchema(),
        data_resources,
        lastupdated=TEST_UPDATE_TAG,
        AWS_ID=TEST_ACCOUNT_ID,
    )

    expected = {
        (
            'test-001', '3kzxbg5sa2',
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:APIGatewayRestAPI)-[:RESOURCE]->(n2:APIGatewayResource) RETURN n1.id, n2.id;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }

    assert actual == expected


@patch.object(
    cartography.intel.aws.apigateway,
    'get_apigateway_rest_apis',
    return_value=tests.data.aws.apigateway.GET_REST_APIS,
)
@patch.object(
    cartography.intel.aws.apigateway,
    'get_rest_api_details',
    return_value=tests.data.aws.apigateway.GET_REST_API_DETAILS,
)
def test_sync_apigateway(mock_get_details, mock_get_apis, neo4j_session):
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
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )

    # Assert REST APIs exist and anonymous access is set correctly
    assert check_nodes(neo4j_session, 'APIGatewayRestAPI', ['id', 'anonymous_access']) == {
        ("test-001", True),
        ("test-002", False),
    }

    # Assert Stages exist
    assert check_nodes(neo4j_session, 'APIGatewayStage', ['id']) == {
        ("arn:aws:apigateway:::test-001/Cartography-testing-infra",),
        ("arn:aws:apigateway:::test-002/Cartography-testing-unit",),
    }

    # Assert Certificates exist
    assert check_nodes(neo4j_session, 'APIGatewayClientCertificate', ['id']) == {
        ("cert-001",),
        ("cert-002",),
    }

    # Assert Resources exist
    assert check_nodes(neo4j_session, 'APIGatewayResource', ['id']) == {
        ("3kzxbg5sa2",),
    }

    # Assert AWS Account to REST API relationships
    assert check_rels(
        neo4j_session,
        'AWSAccount',
        'id',
        'APIGatewayRestAPI',
        'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, 'test-001'),
        (TEST_ACCOUNT_ID, 'test-002'),
    }

    # Assert AWS Account to Stage relationships
    assert check_rels(
        neo4j_session,
        'AWSAccount',
        'id',
        'APIGatewayStage',
        'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, 'arn:aws:apigateway:::test-001/Cartography-testing-infra'),
        (TEST_ACCOUNT_ID, 'arn:aws:apigateway:::test-002/Cartography-testing-unit'),
    }

    # Assert AWS Account to Certificate relationships
    assert check_rels(
        neo4j_session,
        'AWSAccount',
        'id',
        'APIGatewayClientCertificate',
        'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, 'cert-001'),
        (TEST_ACCOUNT_ID, 'cert-002'),
    }
    # Assert AWS Account to Resource relationships
    assert check_rels(
        neo4j_session,
        'AWSAccount',
        'id',
        'APIGatewayResource',
        'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, '3kzxbg5sa2'),
    }
