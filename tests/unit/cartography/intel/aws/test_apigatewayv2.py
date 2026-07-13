from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from botocore.exceptions import EndpointConnectionError

import tests.data.aws.apigatewayv2 as test_data
from cartography.intel.aws import apigatewayv2


def test_transform_apigatewayv2_apis():
    transformed = apigatewayv2.transform_apigatewayv2_apis(test_data.GET_APIS)
    assert transformed[0]["id"] == "api-001"
    assert transformed[0]["protocoltype"] == "HTTP"


def test_get_apigatewayv2_apis_raises_transient_region_failure_on_internal_server_error():
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    paginator = client.get_paginator.return_value
    paginator.paginate.side_effect = ClientError(
        {
            "Error": {
                "Code": "AuthorizerConfigurationException",
                "Message": "Internal server error",
            },
            "ResponseMetadata": {"HTTPStatusCode": 500},
        },
        "GetApis",
    )

    with pytest.raises(apigatewayv2.APIGatewayV2TransientRegionFailure):
        apigatewayv2.get_apigatewayv2_apis(boto3_session, "us-east-1")


def test_get_apigatewayv2_apis_skips_endpoint_connection_error():
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    paginator = client.get_paginator.return_value
    paginator.paginate.side_effect = EndpointConnectionError(
        endpoint_url="https://apigateway.us-iso-east-1.amazonaws.com"
    )

    assert apigatewayv2.get_apigatewayv2_apis(boto3_session, "us-iso-east-1") == []


def test_sync_skips_cleanup_after_transient_region_failure(mocker):
    mocker.patch(
        "cartography.intel.aws.apigatewayv2.sync_apigatewayv2_apis",
        side_effect=apigatewayv2.APIGatewayV2TransientRegionFailure(
            "temporary failure"
        ),
    )
    cleanup = mocker.patch("cartography.intel.aws.apigatewayv2.cleanup")

    apigatewayv2.sync(
        MagicMock(),
        MagicMock(),
        ["us-east-1"],
        "123456789012",
        1,
        {},
    )

    cleanup.assert_not_called()
