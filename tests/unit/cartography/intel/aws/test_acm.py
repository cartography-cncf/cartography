from cartography.intel.aws import acm
from tests.data.aws import acm as test_data


def test_transform_acm_certificates():
    result = acm.transform_acm_certificates(
        [test_data.DESCRIBE_CERTIFICATE["Certificate"]],
        "us-east-1",
    )
    assert len(result) == 1
    cert = result[0]
    assert cert["Arn"] == "arn:aws:acm:us-east-1:000000000000:certificate/test-cert"
    assert cert["DomainName"] == "example.com"
    assert cert["Status"] == "ISSUED"
    assert cert["InUseBy"] == [
        "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/test-lb/abcd/efgh"
    ]
    assert cert["ELBV2ListenerArns"] == [
        "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/test-lb/abcd/efgh"
    ]
