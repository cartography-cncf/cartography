import inspect
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


def test_transform_apigatewayv2_stages_constructs_the_stage_arn():
    # Arrange
    stages = test_data.GET_STAGES_RESPONSE_API_001["Items"]

    # Act
    transformed = apigatewayv2.transform_apigatewayv2_stages(
        stages,
        "us-east-1",
        "api-001",
    )

    # Assert
    # The ARN is constructed because the GetStages response has no ARN member.
    # This is the exact format WAFv2 ListResourcesForWebACL returns for
    # API_GATEWAY associations.
    assert (
        transformed[0]["arn"]
        == "arn:aws:apigateway:us-east-1::/apis/api-001/stages/prod"
    )
    assert (
        transformed[1]["arn"]
        == "arn:aws:apigateway:us-east-1::/apis/api-001/stages/dev"
    )
    assert transformed[0]["apiId"] == "api-001"
    assert transformed[0]["stageName"] == "prod"
    assert transformed[0]["autoDeploy"] is True
    assert transformed[0]["deploymentId"] == "deployment-001"
    assert transformed[0]["clientCertificateId"] == "cert-001"
    # A stage with missing optional members transforms to None values.
    assert transformed[1] == {
        "arn": "arn:aws:apigateway:us-east-1::/apis/api-001/stages/dev",
        "apiId": "api-001",
        "stageName": "dev",
        "autoDeploy": False,
        "deploymentId": None,
        "description": None,
        "createdDate": test_data.STAGE_API_001_DEV["CreatedDate"],
        "lastUpdatedDate": None,
        "apiGatewayManaged": None,
        "clientCertificateId": None,
    }


def test_transform_apigatewayv2_stages_uses_the_region_partition():
    # GovCloud and China ARNs must use their own partition so they match the
    # ARNs WAFv2 ListResourcesForWebACL returns in those partitions.
    stages = [test_data.STAGE_API_001_PROD]

    gov = apigatewayv2.transform_apigatewayv2_stages(stages, "us-gov-west-1", "api-001")
    assert (
        gov[0]["arn"]
        == "arn:aws-us-gov:apigateway:us-gov-west-1::/apis/api-001/stages/prod"
    )

    cn = apigatewayv2.transform_apigatewayv2_stages(stages, "cn-north-1", "api-001")
    assert cn[0]["arn"] == "arn:aws-cn:apigateway:cn-north-1::/apis/api-001/stages/prod"


def test_get_apigatewayv2_stages_returns_stages_keyed_by_api_id():
    # Arrange
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    paginator = client.get_paginator.return_value
    paginator.paginate.return_value = [test_data.GET_STAGES_RESPONSE_API_001]

    # Act
    result = apigatewayv2.get_apigatewayv2_stages(
        boto3_session,
        "us-east-1",
        ["api-001"],
    )

    # Assert
    assert result == {
        "api-001": [test_data.STAGE_API_001_PROD, test_data.STAGE_API_001_DEV],
    }
    client.get_paginator.assert_called_once_with("get_stages")
    paginator.paginate.assert_called_once_with(ApiId="api-001")


def test_get_apigatewayv2_stages_merges_all_pages():
    # Arrange
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    paginator = client.get_paginator.return_value
    paginator.paginate.return_value = [
        {"Items": [test_data.STAGE_API_001_PROD]},
        {"Items": [test_data.STAGE_API_001_DEV]},
    ]

    # Act
    result = apigatewayv2.get_apigatewayv2_stages(
        boto3_session,
        "us-east-1",
        ["api-001"],
    )

    # Assert
    assert result == {
        "api-001": [test_data.STAGE_API_001_PROD, test_data.STAGE_API_001_DEV],
    }


def test_get_apigatewayv2_stages_raises_on_a_non_retryable_error():
    # A failed GetStages must not look like an empty success: cleanup would
    # otherwise delete the API's last-known-good stage nodes. Unwrap the
    # aws_handle_regions decorator (as in test_cloudtrail): region-skippable
    # errors such as AccessDenied are degraded to a regional skip by that
    # shared decorator, like every other AWS connector.
    # Arrange
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    paginator = client.get_paginator.return_value
    paginator.paginate.side_effect = ClientError(
        {
            "Error": {
                "Code": "ValidationException",
                "Message": "invalid request",
            }
        },
        "GetStages",
    )

    # Act and assert
    get_stages_unwrapped = inspect.unwrap(apigatewayv2.get_apigatewayv2_stages)
    with pytest.raises(ClientError):
        get_stages_unwrapped(boto3_session, "us-east-1", ["api-001"])


def test_get_apigatewayv2_stages_raises_transient_region_failure_on_throttling():
    # Arrange
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    paginator = client.get_paginator.return_value
    paginator.paginate.side_effect = ClientError(
        {
            "Error": {"Code": "TooManyRequestsException", "Message": "Slow down"},
            "ResponseMetadata": {"HTTPStatusCode": 429},
        },
        "GetStages",
    )

    # Act and assert
    with pytest.raises(apigatewayv2.APIGatewayV2TransientRegionFailure):
        apigatewayv2.get_apigatewayv2_stages(boto3_session, "us-east-1", ["api-001"])


def test_load_apigatewayv2_stages_loads_the_stage_schema(mocker):
    # Arrange
    load_mock = mocker.patch("cartography.intel.aws.apigatewayv2.load")
    data = apigatewayv2.transform_apigatewayv2_stages(
        test_data.GET_STAGES_RESPONSE_API_001["Items"],
        "us-east-1",
        "api-001",
    )

    # Act
    apigatewayv2.load_apigatewayv2_stages(
        MagicMock(),
        data,
        "us-east-1",
        "123456789012",
        123,
    )

    # Assert
    assert load_mock.call_args.args[1].__class__.__name__ == "APIGatewayV2StageSchema"
    assert load_mock.call_args.args[2] == data
    assert load_mock.call_args.kwargs == {
        "lastupdated": 123,
        "AWS_ID": "123456789012",
        "region": "us-east-1",
    }


def test_cleanup_runs_api_and_stage_cleanup_jobs(mocker):
    # Arrange
    api_job = MagicMock()
    stage_job = MagicMock()
    from_node_schema_mock = mocker.patch.object(
        apigatewayv2.GraphJob,
        "from_node_schema",
        side_effect=[api_job, stage_job],
    )

    # Act
    apigatewayv2.cleanup(MagicMock(), {"UPDATE_TAG": 123, "AWS_ID": "123456789012"})

    # Assert
    schema_names = [
        call_args.args[0].__class__.__name__
        for call_args in from_node_schema_mock.call_args_list
    ]
    assert schema_names == ["APIGatewayV2APISchema", "APIGatewayV2StageSchema"]
    api_job.run.assert_called_once()
    stage_job.run.assert_called_once()
