from datetime import datetime
from datetime import timezone
from typing import Any
from typing import cast
from unittest.mock import call
from unittest.mock import MagicMock

from cartography.intel.aws.ssm import _minimize_allowlisted_prefixes
from cartography.intel.aws.ssm import _normalize_allowlisted_prefixes
from cartography.intel.aws.ssm import get_public_ssm_parameters_by_path
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


def test_get_public_ssm_parameters_by_path_handles_pagination_and_securestring_filtering() -> (
    None
):
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
                {
                    "Name": "/aws/service/bottlerocket/aws-k8s-1.30/x86_64/latest/secret",
                    "Type": "SecureString",
                    "Value": "should-not-be-ingested",
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
        False,
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
