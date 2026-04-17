from datetime import datetime
from datetime import timezone
from typing import Any
from typing import cast
from unittest.mock import call
from unittest.mock import MagicMock

from cartography.intel.aws.ssm import _build_ssm_parameter_id
from cartography.intel.aws.ssm import _normalize_allowlisted_prefixes
from cartography.intel.aws.ssm import _parameter_matches_allowlist_prefixes
from cartography.intel.aws.ssm import get_public_ssm_parameters_by_path
from cartography.intel.aws.ssm import transform_ssm_parameters


def test_normalize_allowlisted_prefixes() -> None:
    assert _normalize_allowlisted_prefixes(
        "/aws/service/bottlerocket/, /aws/service/eks/optimized-ami",
    ) == ["/aws/service/bottlerocket/", "/aws/service/eks/optimized-ami/"]


def test_parameter_matches_allowlist_prefixes() -> None:
    assert _parameter_matches_allowlist_prefixes(
        "/aws/service/bottlerocket/aws-k8s-1.30/x86_64/latest/image_id",
        ["/aws/service/bottlerocket/", "/aws/service/eks/optimized-ami/"],
    )
    assert not _parameter_matches_allowlist_prefixes(
        "/my/private/path",
        ["/aws/service/bottlerocket/", "/aws/service/eks/optimized-ami/"],
    )


def test_get_public_ssm_parameters_by_path_handles_pagination_and_securestring_filtering() -> (
    None
):
    client = MagicMock()
    client.get_parameters_by_path.side_effect = [
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
            "NextToken": "token-1",
        },
        {
            "Parameters": [
                {
                    "Name": "/other/prefix/not-allowlisted",
                    "Type": "String",
                    "Value": "ami-00000",
                },
                {
                    "Name": "/aws/service/bottlerocket/aws-k8s-1.30/x86_64/latest/image_version",
                    "Type": "String",
                    "Value": "1.30.5",
                },
            ],
        },
    ]
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
    assert client.get_parameters_by_path.call_args_list == [
        call(
            Path="/aws/service/bottlerocket/",
            Recursive=True,
            WithDecryption=False,
            MaxResults=10,
        ),
        call(
            Path="/aws/service/bottlerocket/",
            Recursive=True,
            WithDecryption=False,
            MaxResults=10,
            NextToken="token-1",
        ),
    ]


def test_build_ssm_parameter_id_is_deterministic() -> None:
    assert _build_ssm_parameter_id(
        "000000000000",
        "us-west-2",
        "/aws/service/eks/optimized-ami/1.30/amazon-linux-2/recommended/image_id",
    ) == (
        "arn:aws:ssm:us-west-2:000000000000:parameter"
        "/aws/service/eks/optimized-ami/1.30/amazon-linux-2/recommended/image_id"
    )


def test_transform_ssm_parameters_sets_id_and_dates() -> None:
    transformed = transform_ssm_parameters(
        [
            {
                "Name": "/aws/service/bottlerocket/aws-k8s-1.30/x86_64/latest/image_id",
                "Type": "String",
                "Version": 3,
                "Value": "ami-abc123",
                "LastModifiedDate": datetime(2025, 1, 2, tzinfo=timezone.utc),
            }
        ],
        "us-east-1",
        "000000000000",
    )
    assert transformed[0]["Id"] == (
        "arn:aws:ssm:us-east-1:000000000000:parameter"
        "/aws/service/bottlerocket/aws-k8s-1.30/x86_64/latest/image_id"
    )
    assert transformed[0]["LastModifiedDate"] == 1735776000
