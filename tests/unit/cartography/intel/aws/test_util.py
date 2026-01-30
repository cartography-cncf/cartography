import pytest

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
