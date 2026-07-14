from datetime import datetime
from datetime import timezone
from typing import Any
from typing import cast
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.aws.ssm import _minimize_allowlisted_prefixes
from cartography.intel.aws.ssm import _normalize_allowlisted_prefixes
from cartography.intel.aws.ssm import get_public_ssm_parameters_by_path
from cartography.intel.aws.ssm import sync_public_parameters
from cartography.intel.aws.ssm import transform_ssm_parameters


def test_normalize_allowlisted_prefixes() -> None:
    assert _normalize_allowlisted_prefixes(
        "/aws/service/bottlerocket/, /aws/service/eks/optimized-ami, /aws/service/bottlerocket/",
    ) == ["/aws/service/bottlerocket/", "/aws/service/eks/optimized-ami/"]


def test_minimize_allowlisted_prefixes() -> None:
    assert _minimize_allowlisted_prefixes(
        [
            "/aws/service/bottlerocket/",
            "/aws/service/",
            "/aws/service/eks/optimized-ami/",
        ],
    ) == ["/aws/service/"]


def test_get_public_ssm_parameters_by_path_handles_pagination() -> None:
    client = MagicMock()
    paginator = MagicMock()
    paginator.paginate.return_value = [
        {
            "Parameters": [
                {
                    "Name": "/aws/service/bottlerocket/aws-k8s-1.30/x86_64/latest/image_id",
                    "Type": "String",
                    "Value": "ami-12345",
                },
            ],
        },
        {
            "Parameters": [
                {
                    "Name": "/aws/service/bottlerocket/aws-k8s-1.30/x86_64/latest/image_version",
                    "Type": "String",
                    "Value": "1.30.5",
                },
            ],
        },
    ]
    client.get_paginator.return_value = paginator
    boto3_session = MagicMock()
    boto3_session.client.return_value = client

    wrapped_get_public_ssm_parameters_by_path = cast(
        Any,
        get_public_ssm_parameters_by_path,
    ).__wrapped__
    results = wrapped_get_public_ssm_parameters_by_path(
        boto3_session,
        "us-east-1",
        ["/aws/service/bottlerocket/"],
    )

    assert results == [
        {
            "Name": "/aws/service/bottlerocket/aws-k8s-1.30/x86_64/latest/image_id",
            "Type": "String",
            "Value": "ami-12345",
        },
        {
            "Name": "/aws/service/bottlerocket/aws-k8s-1.30/x86_64/latest/image_version",
            "Type": "String",
            "Value": "1.30.5",
        },
    ]
    client.get_paginator.assert_called_once_with("get_parameters_by_path")
    assert paginator.paginate.call_args_list == [
        call(
            Path="/aws/service/bottlerocket/",
            Recursive=True,
            WithDecryption=False,
            PaginationConfig={"PageSize": 10},
        ),
    ]


def test_transform_ssm_parameters_preserves_arn_identity_and_dates() -> None:
    transformed = transform_ssm_parameters(
        [
            {
                "Name": "/aws/service/bottlerocket/aws-k8s-1.30/x86_64/latest/image_id",
                "ARN": "arn:aws:ssm:us-east-1::parameter/aws/service/bottlerocket/aws-k8s-1.30/x86_64/latest/image_id",
                "Type": "String",
                "Version": 3,
                "Value": "ami-abc123",
                "LastModifiedDate": datetime(2025, 1, 2, tzinfo=timezone.utc),
            }
        ],
    )
    assert transformed[0]["ARN"] == (
        "arn:aws:ssm:us-east-1::parameter/aws/service/bottlerocket/"
        "aws-k8s-1.30/x86_64/latest/image_id"
    )
    assert transformed[0]["LastModifiedDate"] == 1735776000


@patch("cartography.intel.aws.ssm.cleanup_public_ssm_parameters")
@patch("cartography.intel.aws.ssm.load_public_ssm_parameters")
@patch("cartography.intel.aws.ssm.get_public_ssm_parameters_by_path")
def test_sync_public_parameters_falls_back_to_next_profile(
    mock_get_parameters,
    mock_load_parameters,
    mock_cleanup,
) -> None:
    # Arrange
    first_session = MagicMock(name="first_session")
    second_session = MagicMock(name="second_session")
    parameter = {
        "Name": "/aws/service/bottlerocket/example",
        "ARN": "arn:aws:ssm:us-east-1::parameter/aws/service/bottlerocket/example",
        "Type": "String",
        "Value": "example",
    }
    mock_get_parameters.side_effect = [[], [parameter]]

    # Act
    sync_public_parameters(
        MagicMock(),
        {"us-east-1": [first_session, second_session]},
        123,
        {
            "UPDATE_TAG": 123,
            "aws_ssm_public_parameter_prefix_allowlist": "/aws/service/bottlerocket/",
        },
    )

    # Assert
    assert mock_get_parameters.call_args_list == [
        call(first_session, "us-east-1", ["/aws/service/bottlerocket/"]),
        call(second_session, "us-east-1", ["/aws/service/bottlerocket/"]),
    ]
    mock_load_parameters.assert_called_once()
    mock_cleanup.assert_called_once()


@patch("cartography.intel.aws.ssm.cleanup_public_ssm_parameters")
@patch("cartography.intel.aws.ssm.load_public_ssm_parameters")
@patch(
    "cartography.intel.aws.ssm.get_public_ssm_parameters_by_path",
    return_value=[],
)
def test_sync_public_parameters_preserves_stale_data_when_region_is_unreadable(
    mock_get_parameters,
    mock_load_parameters,
    mock_cleanup,
) -> None:
    # Act
    sync_public_parameters(
        MagicMock(),
        {"us-east-1": [MagicMock()]},
        123,
        {
            "UPDATE_TAG": 123,
            "aws_ssm_public_parameter_prefix_allowlist": "/aws/service/bottlerocket/",
        },
    )

    # Assert
    mock_get_parameters.assert_called_once()
    mock_load_parameters.assert_not_called()
    mock_cleanup.assert_not_called()
