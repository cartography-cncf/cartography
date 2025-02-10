import pytest

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
