from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.apigateway
import cartography.intel.aws.dynamodb
import cartography.intel.aws.lambda_function
import cartography.intel.aws.s3
import tests.data.aws.apigateway
import tests.data.aws.dynamodb
import tests.data.aws.lambda_function
import tests.data.aws.s3
from cartography.client.core.tx import load
from cartography.models.aws.apigatewaycertificate import (
    APIGatewayClientCertificateSchema,
)
from cartography.models.aws.apigatewayresource import APIGatewayResourceSchema
from cartography.models.aws.apigatewaystage import APIGatewayStageSchema
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_lambdas(neo4j_session, account_id, update_tag, region):
    lambda_functions_data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS
    cartography.intel.aws.lambda_function.load_lambda_functions(
        neo4j_session,
        lambda_functions_data,
        region,
        account_id,
        update_tag,
    )


def _ensure_local_neo4j_has_test_s3_buckets(neo4j_session, account_id, update_tag):
    bucket_list_data = tests.data.aws.s3.LIST_BUCKETS
    cartography.intel.aws.s3.load_s3_buckets(
        neo4j_session,
        bucket_list_data,
        account_id,
        update_tag,
    )


def _ensure_local_neo4j_has_test_dynamodb_tables(
    neo4j_session, boto3_session, account_id, update_tag, common_job_parameters
):
    with patch.object(
        cartography.intel.aws.dynamodb,
        "get_dynamodb_tables",
        return_value=tests.data.aws.dynamodb.LIST_DYNAMODB_TABLES["Tables"],
    ):
        cartography.intel.aws.dynamodb.sync_dynamodb_tables(
            neo4j_session,
            boto3_session,
            TEST_REGION,
            account_id,
            update_tag,
            common_job_parameters,
        )


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
    actual_nodes = {n["r.id"] for n in nodes}

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
        (TEST_ACCOUNT_ID, "test-001"),
        (TEST_ACCOUNT_ID, "test-002"),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AWSAccount)-[:RESOURCE]->(n2:APIGatewayRestAPI) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}

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
    actual_nodes = {n["r.id"] for n in nodes}

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
            "test-001",
            "arn:aws:apigateway:::test-001/Cartography-testing-infra",
        ),
        (
            "test-002",
            "arn:aws:apigateway:::test-002/Cartography-testing-unit",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:APIGatewayRestAPI)-[:ASSOCIATED_WITH]->(n2:APIGatewayStage) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}

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
    actual_nodes = {n["r.id"] for n in nodes}

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
            "arn:aws:apigateway:::test-001/Cartography-testing-infra",
            "cert-001",
        ),
        (
            "arn:aws:apigateway:::test-002/Cartography-testing-unit",
            "cert-002",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:APIGatewayStage)-[:HAS_CERTIFICATE]->(n2:APIGatewayClientCertificate) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}

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
    actual_nodes = {n["r.id"] for n in nodes}

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
            "test-001",
            "3kzxbg5sa2",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:APIGatewayRestAPI)-[:RESOURCE]->(n2:APIGatewayResource) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected


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
@patch.object(
    cartography.intel.aws.apigateway,
    "get_apigateway_methods",
    side_effect=lambda boto3_session, rest_api_id, resource_id, region: [
        response
        for response in [
            tests.data.aws.apigateway.MOCK_GET_METHOD_RESPONSES.get(
                (rest_api_id, resource_id, "GET")
            ),
            tests.data.aws.apigateway.MOCK_GET_METHOD_RESPONSES.get(
                (rest_api_id, resource_id, "POST")
            ),
            tests.data.aws.apigateway.MOCK_GET_METHOD_RESPONSES.get(
                (rest_api_id, resource_id, "PUT")
            ),
            tests.data.aws.apigateway.MOCK_GET_METHOD_RESPONSES.get(
                (rest_api_id, resource_id, "DELETE")
            ),
            tests.data.aws.apigateway.MOCK_GET_METHOD_RESPONSES.get(
                (rest_api_id, resource_id, "PATCH")
            ),
        ]
        if response is not None
    ],
)
def test_sync_apigateway(
    mock_get_apis,
    mock_get_details,
    mock_get_methods,
    neo4j_session,
):
    """
    Verify that API Gateway resources are properly synced
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    _ensure_local_neo4j_has_test_lambdas(
        neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG, TEST_REGION
    )
    _ensure_local_neo4j_has_test_s3_buckets(
        neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG
    )
    _ensure_local_neo4j_has_test_dynamodb_tables(
        neo4j_session,
        boto3_session,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Act
    cartography.intel.aws.apigateway.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert REST APIs exist and anonymous access is set correctly
    assert check_nodes(
        neo4j_session,
        "APIGatewayRestAPI",
        ["id", "anonymous_access"],
    ) == {
        ("test-001", True),
        ("test-002", False),
    }

    # Assert Stages exist
    assert check_nodes(neo4j_session, "APIGatewayStage", ["id"]) == {
        ("arn:aws:apigateway:::test-001/Cartography-testing-infra",),
        ("arn:aws:apigateway:::test-002/Cartography-testing-unit",),
    }

    # Assert Certificates exist
    assert check_nodes(neo4j_session, "APIGatewayClientCertificate", ["id"]) == {
        ("cert-001",),
        ("cert-002",),
    }

    # Assert Resources exist
    assert check_nodes(neo4j_session, "APIGatewayResource", ["id"]) == {
        ("3kzxbg5sa2",),
    }

    # Assertions FOR APIGatewayMethod(GET, POST, PUT, DELETE, PATCH)
    lambda_list_data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS
    lambda_arn_1 = lambda_list_data[0]["FunctionArn"]
    lambda_arn_2 = lambda_list_data[1]["FunctionArn"]

    s3_bucket_list_data = tests.data.aws.s3.LIST_BUCKETS
    s3_bucket_name_1 = s3_bucket_list_data["Buckets"][0]["Name"]

    dynamodb_list_data = tests.data.aws.dynamodb.LIST_DYNAMODB_TABLES["Tables"]
    dynamodb_table_arn_1 = dynamodb_list_data[0]["Table"]["TableArn"]

    expected_method_nodes = {
        ("test-001|3kzxbg5sa2|GET", "NONE", False, lambda_arn_1, None, None),
        ("test-001|3kzxbg5sa2|POST", "AWS_IAM", True, lambda_arn_2, None, None),
        ("test-001|3kzxbg5sa2|PUT", "CUSTOM", False, None, None, None),
        ("test-001|3kzxbg5sa2|DELETE", "AWS_IAM", False, None, s3_bucket_name_1, None),
        (
            "test-001|3kzxbg5sa2|PATCH",
            "AWS_IAM",
            True,
            None,
            None,
            dynamodb_table_arn_1,
        ),
    }
    assert (
        check_nodes(
            neo4j_session,
            "APIGatewayMethod",
            [
                "id",
                "authorization_type",
                "api_key_required",
                "lambda_function_arn",
                "s3_bucket_name",
                "dynamodb_table_arn",
            ],
        )
        == expected_method_nodes
    )

    # Assert APIGatewayResource to APIGatewayMethod relationships (:RESOURCE for cleanup)
    expected_resource_method_rels = {
        ("3kzxbg5sa2", "test-001|3kzxbg5sa2|GET"),
        ("3kzxbg5sa2", "test-001|3kzxbg5sa2|POST"),
        ("3kzxbg5sa2", "test-001|3kzxbg5sa2|PUT"),
        ("3kzxbg5sa2", "test-001|3kzxbg5sa2|DELETE"),
        ("3kzxbg5sa2", "test-001|3kzxbg5sa2|PATCH"),
    }
    assert (
        check_rels(
            neo4j_session,
            "APIGatewayResource",
            "id",
            "APIGatewayMethod",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_resource_method_rels
    )

    # Assert APIGatewayMethod to AWSLambda relationships (:INVOKES)
    expected_invokes_rels = {
        ("test-001|3kzxbg5sa2|GET", lambda_arn_1),
        ("test-001|3kzxbg5sa2|POST", lambda_arn_2),
    }
    assert (
        check_rels(
            neo4j_session,
            "APIGatewayMethod",
            "id",
            "AWSLambda",
            "id",
            "INVOKES",
            rel_direction_right=True,
        )
        == expected_invokes_rels
    )

    # Assert APIGatewayMethod to S3Bucket relationships (:ACCESSES)
    expected_s3_access_rels = {
        ("test-001|3kzxbg5sa2|DELETE", s3_bucket_name_1),
    }
    assert (
        check_rels(
            neo4j_session,
            "APIGatewayMethod",
            "id",
            "S3Bucket",
            "id",
            "ACCESSES",
            rel_direction_right=True,
        )
        == expected_s3_access_rels
    )

    # Assert APIGatewayMethod to DynamoDBTable relationships (:ACCESSES)
    expected_ddb_access_rels = {
        ("test-001|3kzxbg5sa2|PATCH", dynamodb_table_arn_1),
    }
    assert (
        check_rels(
            neo4j_session,
            "APIGatewayMethod",
            "id",
            "DynamoDBTable",
            "id",
            "ACCESSES",
            rel_direction_right=True,
        )
        == expected_ddb_access_rels
    )

    # Assert AWS Account to REST API relationships
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "APIGatewayRestAPI",
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
        "APIGatewayStage",
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
        "APIGatewayClientCertificate",
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
        "APIGatewayResource",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "3kzxbg5sa2"),
    }
