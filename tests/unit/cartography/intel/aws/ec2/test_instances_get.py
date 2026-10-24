from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import EndpointConnectionError
from botocore.exceptions import ReadTimeoutError
from botocore.exceptions import SSLError
from botocore.parsers import ResponseParserError

from cartography.intel.aws.ec2.instances import EC2RegionDiscoveryFailure
from cartography.intel.aws.ec2.instances import get_ec2_instances


@pytest.mark.parametrize(
    "error",
    [
        ClientError({"Error": {"Code": code}}, "DescribeInstances")
        for code in (
            "AccessDenied",
            "UnauthorizedOperation",
            "InternalServerErrorException",
        )
    ]
    + [
        error_type(endpoint_url="https://ec2.example.invalid", error="synthetic")
        for error_type in (
            ConnectTimeoutError,
            EndpointConnectionError,
            ReadTimeoutError,
            SSLError,
        )
    ],
)
def test_get_instances_distinguishes_regional_failure_from_empty(error):
    # Arrange
    provider = MagicMock()
    provider.client.side_effect = error

    # Act and assert
    with pytest.raises(EC2RegionDiscoveryFailure) as failure:
        get_ec2_instances(provider, "us-east-1")
    assert failure.value.__cause__ is error
    provider.client.assert_called_once()


@pytest.mark.parametrize(
    "error",
    [
        ClientError({"Error": {"Code": "ThrottlingException"}}, "DescribeInstances"),
        ResponseParserError("Synthetic malformed response"),
    ],
)
def test_get_instances_retains_api_retries(error):
    # Arrange
    provider = MagicMock()
    paginator = provider.client.return_value.get_paginator.return_value
    paginator.paginate.side_effect = [error, [{"Reservations": []}]]

    # Act
    reservations = get_ec2_instances(provider, "us-east-1")

    # Assert
    assert reservations == []
    assert paginator.paginate.call_count == 2


def test_get_instances_retains_invalid_token_guidance():
    # Arrange
    provider = MagicMock()
    provider.client.side_effect = ClientError(
        {"Error": {"Code": "InvalidToken"}}, "DescribeInstances"
    )

    # Act and assert
    with pytest.raises(RuntimeError, match="AWS_STS_REGIONAL_ENDPOINTS=regional"):
        get_ec2_instances(provider, "us-east-1")
