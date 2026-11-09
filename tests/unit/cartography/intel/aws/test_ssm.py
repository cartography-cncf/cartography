from datetime import datetime
from datetime import timezone
from typing import Any
from typing import cast
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError
from pytest_mock import MockerFixture

from cartography.intel.aws.ssm import _minimize_allowlisted_prefixes
from cartography.intel.aws.ssm import _normalize_allowlisted_prefixes
from cartography.intel.aws.ssm import get_instance_patches
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


def _patch_states_paginator(patched_instance_ids: set[str]) -> MagicMock:
    def paginate(InstanceIds: list[str]) -> list[dict[str, Any]]:
        if len(InstanceIds) > 50:
            raise ClientError(
                {"Error": {"Code": "ValidationException", "Message": "Too many IDs"}},
                "DescribeInstancePatchStates",
            )
        return [
            {
                "InstancePatchStates": [
                    {"InstanceId": instance_id}
                    for instance_id in InstanceIds
                    if instance_id in patched_instance_ids
                ],
            },
        ]

    paginator = MagicMock()
    paginator.paginate.side_effect = paginate
    return paginator


def test_get_instance_patches_skips_instances_without_a_patch_state() -> None:
    # Arrange
    instance_ids = [f"i-{n:02d}" for n in range(60)]
    patches_paginator = MagicMock()
    patches_paginator.paginate.side_effect = lambda InstanceId: [
        {"Patches": [{"Title": f"patch-for-{InstanceId}"}]},
    ]
    patch_states_paginator = _patch_states_paginator({"i-07", "i-55"})
    boto3_session = MagicMock()
    boto3_session.client.return_value.get_paginator.side_effect = {
        "describe_instance_patch_states": patch_states_paginator,
        "describe_instance_patches": patches_paginator,
    }.get

    # Act
    patches = get_instance_patches(boto3_session, "us-east-1", instance_ids)

    # Assert
    assert patch_states_paginator.paginate.call_count == 2
    assert [
        c.kwargs["InstanceId"] for c in patches_paginator.paginate.call_args_list
    ] == ["i-07", "i-55"]
    assert patches == [
        {"Title": "patch-for-i-07", "_instance_id": "i-07"},
        {"Title": "patch-for-i-55", "_instance_id": "i-55"},
    ]


@pytest.mark.parametrize(  # type: ignore[misc]
    ("error_code", "expected_calls", "expected_patches"),
    [
        pytest.param(
            "ThrottlingException",
            ["i-01", "i-02", "i-02", "i-03"],
            [
                {"Title": "patch-1", "_instance_id": "i-01"},
                {"Title": "patch-2", "_instance_id": "i-02"},
                {"Title": "patch-3", "_instance_id": "i-03"},
            ],
            id="throttle-resumes-from-the-throttled-instance",
        ),
        pytest.param(
            "AccessDeniedException",
            ["i-01", "i-02"],
            [],
            id="access-denied-skips-the-region-without-retrying",
        ),
    ],
)
def test_get_instance_patches_handles_error_on_second_instance(
    mocker: MockerFixture,
    error_code: str,
    expected_calls: list[str],
    expected_patches: list[dict[str, str]],
) -> None:
    # Arrange
    mocker.patch("time.sleep")
    paginator = MagicMock()
    paginator.paginate.side_effect = [
        [{"Patches": [{"Title": "patch-1"}]}],
        ClientError(
            {"Error": {"Code": error_code, "Message": "Request failed"}},
            "DescribeInstancePatches",
        ),
        [{"Patches": [{"Title": "patch-2"}]}],
        [{"Patches": [{"Title": "patch-3"}]}],
    ]
    boto3_session = MagicMock()
    boto3_session.client.return_value.get_paginator.side_effect = {
        "describe_instance_patch_states": _patch_states_paginator(
            {"i-01", "i-02", "i-03"},
        ),
        "describe_instance_patches": paginator,
    }.get

    # Act
    patches = get_instance_patches(
        boto3_session,
        "us-east-1",
        ["i-01", "i-02", "i-03"],
    )

    # Assert
    assert [
        c.kwargs["InstanceId"] for c in paginator.paginate.call_args_list
    ] == expected_calls
    assert patches == expected_patches


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
