from unittest.mock import ANY
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from botocore.exceptions import EndpointConnectionError

from cartography.intel.aws import lambda_function
from cartography.intel.aws.util.botocore_config import get_lambda_botocore_config
from tests.data.aws.lambda_function import FUNCTION_URL_CONFIGS_BY_NAME
from tests.data.aws.lambda_function import GET_FUNCTION_URL_CONFIG_AWS_IAM
from tests.data.aws.lambda_function import GET_FUNCTION_URL_CONFIG_NONE
from tests.data.aws.lambda_function import LIST_LAMBDA_FUNCTIONS
from tests.data.aws.lambda_function import LIST_LAMBDA_PERMISSIONS


def _client_error(code: str, message: str, status_code: int) -> ClientError:
    return ClientError(
        {
            "Error": {"Code": code, "Message": message},
            "ResponseMetadata": {"HTTPStatusCode": status_code},
        },
        "ListEventSourceMappings",
    )


def _mock_get_function_url_config(**kwargs):
    """Return the mocked URL config, or raise not-found like the real API."""
    url_config = FUNCTION_URL_CONFIGS_BY_NAME.get(kwargs["FunctionName"])
    if url_config is None:
        raise _client_error(
            "ResourceNotFoundException",
            "The resource you requested does not exist.",
            404,
        )
    return url_config


def test_get_event_source_mappings_raises_transient_failure_after_retry_exhaustion():
    client = MagicMock()
    paginator = client.get_paginator.return_value
    paginator.paginate.side_effect = _client_error(
        "ServiceException",
        "An error occurred and the request cannot be processed.",
        500,
    )

    with pytest.raises(lambda_function.LambdaSubResourceTransientFailure):
        lambda_function.get_event_source_mappings(LIST_LAMBDA_FUNCTIONS[0], client)


def test_get_lambda_data_uses_lambda_retry_profile():
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    client.get_paginator.return_value.paginate.return_value = []

    lambda_function.get_lambda_data(boto3_session, "us-east-1")

    assert (
        boto3_session.client.call_args.kwargs["config"] == get_lambda_botocore_config()
    )


def test_get_lambda_image_uris_raises_transient_failure_after_retry_exhaustion():
    image_lambda = dict(LIST_LAMBDA_FUNCTIONS[0], PackageType="Image")
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    client.get_function.side_effect = _client_error(
        "ServiceException",
        "An error occurred and the request cannot be processed.",
        500,
    )

    with pytest.raises(lambda_function.LambdaTransientRegionFailure):
        lambda_function.get_lambda_image_uris(
            boto3_session,
            [image_lambda],
            "us-east-1",
        )


def test_get_lambda_image_uris_uses_lambda_retry_profile():
    image_lambda = dict(LIST_LAMBDA_FUNCTIONS[0], PackageType="Image")
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    client.get_function.return_value = {"Code": {}}

    lambda_function.get_lambda_image_uris(
        boto3_session,
        [image_lambda],
        "us-east-1",
    )

    assert (
        boto3_session.client.call_args.kwargs["config"] == get_lambda_botocore_config()
    )


def test_get_lambda_data_skips_endpoint_connection_error():
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    client.get_paginator.return_value.paginate.side_effect = EndpointConnectionError(
        endpoint_url="https://lambda.us-iso-east-1.amazonaws.com"
    )

    assert lambda_function.get_lambda_data(boto3_session, "us-iso-east-1") == []


def test_get_function_url_config_returns_none_on_not_found():
    # Arrange
    client = MagicMock()
    client.get_function_url_config.side_effect = _client_error(
        "ResourceNotFoundException",
        "not found",
        404,
    )

    # Act and assert
    assert lambda_function.get_function_url_config(client, "sample-function-3") is None


def test_get_function_url_config_returns_response_when_configured():
    # Arrange
    client = MagicMock()
    client.get_function_url_config.return_value = GET_FUNCTION_URL_CONFIG_AWS_IAM

    # Act
    response = lambda_function.get_function_url_config(client, "sample-function-1")

    # Assert
    assert response == GET_FUNCTION_URL_CONFIG_AWS_IAM
    client.get_function_url_config.assert_called_once_with(
        FunctionName="sample-function-1"
    )


def test_get_lambda_data_attaches_function_url_config_fields():
    # Arrange
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    client.get_paginator.return_value.paginate.return_value = [
        {"Functions": [dict(f) for f in LIST_LAMBDA_FUNCTIONS[:3]]}
    ]
    client.get_function_url_config.side_effect = _mock_get_function_url_config

    # Act
    functions = lambda_function.get_lambda_data(boto3_session, "us-west-2")

    # Assert
    assert functions[0]["FunctionUrl"] == GET_FUNCTION_URL_CONFIG_AWS_IAM["FunctionUrl"]
    assert functions[0]["FunctionUrlAuthType"] == "AWS_IAM"
    assert functions[1]["FunctionUrl"] == GET_FUNCTION_URL_CONFIG_NONE["FunctionUrl"]
    assert functions[1]["FunctionUrlAuthType"] == "NONE"
    # sample-function-3 has no function URL config: the fields stay absent.
    assert "FunctionUrl" not in functions[2]
    assert "FunctionUrlAuthType" not in functions[2]


def test_get_lambda_data_tolerates_missing_function_url_configs():
    # Arrange
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    client.get_paginator.return_value.paginate.return_value = [
        {"Functions": [dict(LIST_LAMBDA_FUNCTIONS[2])]}
    ]
    client.get_function_url_config.side_effect = _client_error(
        "ResourceNotFoundException",
        "not found",
        404,
    )

    # Act
    functions = lambda_function.get_lambda_data(boto3_session, "us-west-2")

    # Assert
    assert functions == [LIST_LAMBDA_FUNCTIONS[2]]
    assert "FunctionUrl" not in functions[0]
    assert "FunctionUrlAuthType" not in functions[0]


def test_get_lambda_data_raises_transient_failure_after_url_config_retry_exhaustion():
    # Arrange
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    client.get_paginator.return_value.paginate.return_value = [
        {"Functions": [dict(LIST_LAMBDA_FUNCTIONS[0])]}
    ]
    client.get_function_url_config.side_effect = _client_error(
        "TooManyRequestsException",
        "Rate exceeded",
        429,
    )

    # Act and assert
    with pytest.raises(lambda_function.LambdaTransientRegionFailure):
        lambda_function.get_lambda_data(boto3_session, "us-east-1")


def test_transform_lambda_functions_passes_function_url_fields_through():
    # Arrange
    expected_url = GET_FUNCTION_URL_CONFIG_AWS_IAM["FunctionUrl"]
    functions = [
        dict(
            LIST_LAMBDA_FUNCTIONS[0],
            FunctionUrl=expected_url,
            FunctionUrlAuthType="AWS_IAM",
        ),
        dict(LIST_LAMBDA_FUNCTIONS[1]),
    ]

    # Act
    transformed = lambda_function.transform_lambda_functions(
        functions,
        LIST_LAMBDA_PERMISSIONS,
        {},
        "us-west-2",
    )

    # Assert
    assert transformed[0]["functionurl"] == expected_url
    assert transformed[0]["functionurlauthtype"] == "AWS_IAM"
    # Functions without a URL config load None for both fields without crashing.
    assert transformed[1]["functionurl"] is None
    assert transformed[1]["functionurlauthtype"] is None


def test_get_lambda_permissions_uses_lambda_retry_profile():
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    client.get_policy.side_effect = _client_error(
        "ResourceNotFoundException",
        "not found",
        404,
    )

    lambda_function.get_lambda_permissions(
        LIST_LAMBDA_FUNCTIONS[:1],
        boto3_session,
        "us-east-1",
    )

    assert (
        boto3_session.client.call_args.kwargs["config"] == get_lambda_botocore_config()
    )


def test_get_lambda_permissions_raises_transient_region_failure_after_retry_exhaustion():
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    client.get_policy.side_effect = _client_error(
        "TooManyRequestsException",
        "Rate exceeded",
        429,
    )

    with pytest.raises(lambda_function.LambdaTransientRegionFailure):
        lambda_function.get_lambda_permissions(
            LIST_LAMBDA_FUNCTIONS[:1],
            boto3_session,
            "us-east-1",
        )


def test_sync_event_source_mappings_skips_failed_function_and_marks_cleanup_unsafe(
    mocker,
):
    load_mappings = mocker.patch(
        "cartography.intel.aws.lambda_function.load_lambda_event_source_mappings"
    )

    def _side_effect(lambda_fn, _client):
        if lambda_fn["FunctionName"] == "sample-function-2":
            raise lambda_function.LambdaSubResourceTransientFailure("temporary failure")
        return [{"UUID": lambda_fn["FunctionName"]}]

    mocker.patch(
        "cartography.intel.aws.lambda_function.get_event_source_mappings",
        side_effect=_side_effect,
    )

    cleanup_safe = lambda_function.sync_event_source_mappings(
        MagicMock(),
        LIST_LAMBDA_FUNCTIONS[:2],
        MagicMock(),
        "123456789012",
        1,
    )

    assert cleanup_safe is False
    load_mappings.assert_called_once_with(
        ANY,
        [{"UUID": "sample-function-1"}],
        "123456789012",
        1,
    )


def test_sync_preserves_function_cleanup_after_transient_subresource_failure(
    mocker,
):
    mocker.patch(
        "cartography.intel.aws.lambda_function.get_lambda_data",
        return_value=LIST_LAMBDA_FUNCTIONS[:1],
    )
    mocker.patch(
        "cartography.intel.aws.lambda_function.get_lambda_permissions",
        return_value={
            LIST_LAMBDA_FUNCTIONS[0]["FunctionArn"]: {
                "AnonymousAccess": False,
                "AnonymousActions": [],
            }
        },
    )
    mocker.patch(
        "cartography.intel.aws.lambda_function.get_lambda_image_uris",
        return_value={},
    )
    mocker.patch("cartography.intel.aws.lambda_function.load_lambda_functions")
    mocker.patch(
        "cartography.intel.aws.lambda_function.sync_aliases",
        return_value=True,
    )
    mocker.patch(
        "cartography.intel.aws.lambda_function.sync_event_source_mappings",
        return_value=False,
    )
    mocker.patch("cartography.intel.aws.lambda_function.sync_lambda_layers")
    cleanup = mocker.patch("cartography.intel.aws.lambda_function.cleanup_lambda")

    lambda_function.sync(
        MagicMock(),
        MagicMock(),
        ["us-east-1"],
        "123456789012",
        1,
        {},
    )

    cleanup.assert_called_once_with(
        ANY,
        {},
        aliases_cleanup_safe=True,
        event_source_mappings_cleanup_safe=False,
        layers_cleanup_safe=True,
        functions_cleanup_safe=True,
    )


def test_sync_skips_cleanup_after_transient_region_failure(mocker):
    mocker.patch(
        "cartography.intel.aws.lambda_function.get_lambda_data",
        side_effect=lambda_function.LambdaTransientRegionFailure("temporary failure"),
    )
    cleanup = mocker.patch("cartography.intel.aws.lambda_function.cleanup_lambda")

    lambda_function.sync(
        MagicMock(),
        MagicMock(),
        ["us-east-1"],
        "123456789012",
        1,
        {},
    )

    cleanup.assert_called_once_with(
        ANY,
        {},
        aliases_cleanup_safe=False,
        event_source_mappings_cleanup_safe=False,
        layers_cleanup_safe=False,
        functions_cleanup_safe=False,
    )


def test_sync_skips_cleanup_after_transient_image_metadata_failure(mocker):
    mocker.patch(
        "cartography.intel.aws.lambda_function.get_lambda_data",
        return_value=[dict(LIST_LAMBDA_FUNCTIONS[0], PackageType="Image")],
    )
    mocker.patch(
        "cartography.intel.aws.lambda_function.get_lambda_permissions",
        return_value={
            LIST_LAMBDA_FUNCTIONS[0]["FunctionArn"]: {
                "AnonymousAccess": False,
                "AnonymousActions": [],
            }
        },
    )
    mocker.patch(
        "cartography.intel.aws.lambda_function.get_lambda_image_uris",
        side_effect=lambda_function.LambdaTransientRegionFailure("temporary failure"),
    )
    load_lambda_functions = mocker.patch(
        "cartography.intel.aws.lambda_function.load_lambda_functions"
    )
    cleanup = mocker.patch("cartography.intel.aws.lambda_function.cleanup_lambda")

    lambda_function.sync(
        MagicMock(),
        MagicMock(),
        ["us-east-1"],
        "123456789012",
        1,
        {},
    )

    load_lambda_functions.assert_not_called()
    cleanup.assert_called_once_with(
        ANY,
        {},
        aliases_cleanup_safe=False,
        event_source_mappings_cleanup_safe=False,
        layers_cleanup_safe=False,
        functions_cleanup_safe=False,
    )


def test_sync_skips_cleanup_after_transient_policy_failure(mocker):
    mocker.patch(
        "cartography.intel.aws.lambda_function.get_lambda_data",
        return_value=LIST_LAMBDA_FUNCTIONS[:1],
    )
    mocker.patch(
        "cartography.intel.aws.lambda_function.get_lambda_permissions",
        side_effect=lambda_function.LambdaTransientRegionFailure("temporary failure"),
    )
    load_lambda_functions = mocker.patch(
        "cartography.intel.aws.lambda_function.load_lambda_functions"
    )
    sync_aliases = mocker.patch("cartography.intel.aws.lambda_function.sync_aliases")
    sync_event_source_mappings = mocker.patch(
        "cartography.intel.aws.lambda_function.sync_event_source_mappings"
    )
    sync_lambda_layers = mocker.patch(
        "cartography.intel.aws.lambda_function.sync_lambda_layers"
    )
    cleanup = mocker.patch("cartography.intel.aws.lambda_function.cleanup_lambda")

    lambda_function.sync(
        MagicMock(),
        MagicMock(),
        ["us-east-1"],
        "123456789012",
        1,
        {},
    )

    load_lambda_functions.assert_not_called()
    sync_aliases.assert_not_called()
    sync_event_source_mappings.assert_not_called()
    sync_lambda_layers.assert_not_called()
    cleanup.assert_called_once_with(
        ANY,
        {},
        aliases_cleanup_safe=False,
        event_source_mappings_cleanup_safe=False,
        layers_cleanup_safe=False,
        functions_cleanup_safe=False,
    )
