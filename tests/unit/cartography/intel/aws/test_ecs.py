from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import EndpointConnectionError
from botocore.exceptions import ReadTimeoutError
from botocore.parsers import ResponseParserError

from cartography.intel.aws import ecs


@pytest.mark.parametrize(
    "getter,kwargs",
    [
        (ecs.get_ecs_cluster_arns, {}),
        (ecs.get_ecs_clusters, {"cluster_arns": ["cluster"]}),
        (ecs.get_ecs_container_instances, {"cluster_arn": "cluster"}),
        (ecs.get_ecs_services, {"cluster_arn": "cluster"}),
        (ecs.get_ecs_task_definitions, {"tasks": []}),
        (ecs.get_ecs_tasks, {"cluster_arn": "cluster"}),
    ],
)
@pytest.mark.parametrize(
    "exception", [ConnectTimeoutError, EndpointConnectionError, ReadTimeoutError]
)
def test_ecs_getters_distinguish_transport_failure_from_empty(
    getter, kwargs, exception
):
    # Arrange
    provider = MagicMock()
    error = exception(endpoint_url="https://ecs.example.invalid")
    provider.client.side_effect = error

    # Act and assert: no empty-list fallback or extra transport retry.
    with pytest.raises(ecs.ECSTransientRegionFailure) as failure:
        getter(boto3_session=provider, region="us-east-1", **kwargs)
    assert failure.value.__cause__ is error
    provider.client.assert_called_once()


@pytest.mark.parametrize(
    "error",
    [
        ClientError({"Error": {"Code": "ThrottlingException"}}, "ListClusters"),
        ResponseParserError("Synthetic malformed response"),
    ],
)
def test_ecs_getter_retains_aws_handle_regions_retries(error):
    # Arrange: the API fails once after the SDK's own retries, then succeeds.
    provider = MagicMock()
    paginator = provider.client.return_value.get_paginator.return_value
    paginator.paginate.side_effect = [error, [{"clusterArns": ["cluster"]}]]

    # Act
    result = ecs.get_ecs_cluster_arns(provider, "us-east-1")

    # Assert: the outer getter retry is still present.
    assert result == ["cluster"]
    assert paginator.paginate.call_count == 2


@pytest.mark.parametrize(
    "message",
    ["Synthetic denial", "Synthetic explicit deny in a service control policy"],
)
def test_ecs_getter_retains_access_denial_policy(message, caplog):
    # Arrange
    provider = MagicMock()
    provider.client.side_effect = ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": message}},
        "ListClusters",
    )

    # Act and assert: denial remains an empty result with the original diagnostic.
    assert ecs.get_ecs_cluster_arns(provider, "us-east-1") == []
    provider.client.assert_called_once()
    assert message in caplog.text


def test_ecs_getter_retains_invalid_token_guidance():
    # Arrange
    provider = MagicMock()
    provider.client.side_effect = ClientError(
        {"Error": {"Code": "InvalidToken"}}, "ListClusters"
    )

    # Act and assert
    with pytest.raises(RuntimeError, match="AWS_STS_REGIONAL_ENDPOINTS=regional"):
        ecs.get_ecs_cluster_arns(provider, "us-east-1")
    provider.client.assert_called_once()


def test_ecs_getter_preserves_handled_server_failure():
    # Arrange: this server error is normally swallowed by aws_handle_regions.
    provider = MagicMock()
    error = ClientError(
        {"Error": {"Code": "InternalServerErrorException"}}, "ListClusters"
    )
    provider.client.return_value.get_paginator.return_value.paginate.side_effect = error

    # Act and assert: distinguish failure from an authoritative empty inventory.
    with pytest.raises(ecs.ECSTransientRegionFailure) as failure:
        ecs.get_ecs_cluster_arns(provider, "us-east-1")
    assert failure.value.__cause__ is error
    provider.client.assert_called_once()
