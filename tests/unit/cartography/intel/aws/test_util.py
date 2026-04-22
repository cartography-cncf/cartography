from unittest.mock import MagicMock

import pytest
from botocore.exceptions import UnknownRegionError

from cartography.intel.aws.util.common import (
    filter_regions_to_supported_service_regions,
)
from cartography.intel.aws.util.common import parse_and_validate_aws_regions
from cartography.intel.aws.util.common import parse_and_validate_aws_requested_syncs


def test_parse_and_validate_requested_syncs():
    no_spaces = "ec2:instance,s3,rds,iam"
    assert parse_and_validate_aws_requested_syncs(no_spaces) == [
        "ec2:instance",
        "s3",
        "rds",
        "iam",
    ]

    mismatch_spaces = "ec2:subnet, eks,kms"
    assert parse_and_validate_aws_requested_syncs(mismatch_spaces) == [
        "ec2:subnet",
        "eks",
        "kms",
    ]

    sync_that_does_not_exist = "lambda_function, thisfuncdoesnotexist, route53"
    with pytest.raises(ValueError):
        parse_and_validate_aws_requested_syncs(sync_that_does_not_exist)

    absolute_garbage = "#@$@#RDFFHKjsdfkjsd,KDFJHW#@,"
    with pytest.raises(ValueError):
        parse_and_validate_aws_requested_syncs(absolute_garbage)


def test_parse_and_validate_aws_regions():
    # Test basic comma-separated input
    basic_input = "us-east-1,us-west-2,eu-west-1"
    assert parse_and_validate_aws_regions(basic_input) == [
        "us-east-1",
        "us-west-2",
        "eu-west-1",
    ]

    # Test input with spaces
    spaced_input = "us-east-1, us-west-2, eu-west-1"
    assert parse_and_validate_aws_regions(spaced_input) == [
        "us-east-1",
        "us-west-2",
        "eu-west-1",
    ]

    # Test empty input
    empty_input = ""
    with pytest.raises(
        ValueError, match="`aws-regions` was set but no regions were specified"
    ):
        parse_and_validate_aws_regions(empty_input)

    # Test input with empty elements
    empty_elements = "us-east-1,,us-west-2,"
    assert parse_and_validate_aws_regions(empty_elements) == ["us-east-1", "us-west-2"]

    # Test single region input
    single_region = "us-east-1"
    assert parse_and_validate_aws_regions(single_region) == ["us-east-1"]

    # Test input with only empty elements
    only_empty = ",,"
    with pytest.raises(
        ValueError, match="`aws-regions` was set but no regions were specified"
    ):
        parse_and_validate_aws_regions(only_empty)


def test_filter_regions_to_supported_service_regions_limits_partition_queries():
    boto3_session = MagicMock()

    def _get_partition_for_region(region):
        return {
            "us-east-1": "aws",
            "us-gov-west-1": "aws-us-gov",
            "ca-west-1": "aws",
        }[region]

    boto3_session.get_partition_for_region.side_effect = _get_partition_for_region
    boto3_session.get_available_regions.side_effect = (
        lambda service_name, partition_name: {
            "aws": ["us-east-1", "us-west-2"],
            "aws-us-gov": ["us-gov-west-1"],
        }[partition_name]
    )

    filtered_regions, unsupported_regions = filter_regions_to_supported_service_regions(
        boto3_session,
        "codebuild",
        ["us-east-1", "us-gov-west-1", "ca-west-1"],
    )

    assert filtered_regions == ["us-east-1", "us-gov-west-1"]
    assert unsupported_regions == ["ca-west-1"]
    assert boto3_session.get_available_regions.call_count == 2
    boto3_session.get_available_regions.assert_any_call(
        "codebuild",
        partition_name="aws",
    )
    boto3_session.get_available_regions.assert_any_call(
        "codebuild",
        partition_name="aws-us-gov",
    )


def test_filter_regions_to_supported_service_regions_falls_back_when_unusable():
    boto3_session = MagicMock()
    boto3_session.get_partition_for_region.return_value = "aws"
    boto3_session.get_available_regions.return_value = []

    filtered_regions, unsupported_regions = filter_regions_to_supported_service_regions(
        boto3_session,
        "bedrock",
        ["us-east-1", "us-west-2"],
    )

    assert filtered_regions == ["us-east-1", "us-west-2"]
    assert unsupported_regions == []


def test_filter_regions_to_supported_service_regions_skips_unknown_regions_and_uses_known_partition():
    boto3_session = MagicMock()

    def _get_partition_for_region(region):
        if region == "not-a-region":
            raise UnknownRegionError(
                region_name=region,
                error_msg="No partition found for provided region_name.",
            )
        return "aws"

    boto3_session.get_partition_for_region.side_effect = _get_partition_for_region
    boto3_session.get_available_regions.return_value = ["us-east-1", "me-south-1"]

    filtered_regions, unsupported_regions = filter_regions_to_supported_service_regions(
        boto3_session,
        "sagemaker",
        ["us-east-1", "not-a-region"],
    )

    assert filtered_regions == ["us-east-1"]
    assert unsupported_regions == ["not-a-region"]
    boto3_session.get_available_regions.assert_called_once_with(
        "sagemaker",
        partition_name="aws",
    )
