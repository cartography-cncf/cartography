from unittest.mock import call
from unittest.mock import MagicMock

from cartography.intel.aws import acm
from tests.data.aws import acm as test_data


def test_get_acm_certificates_includes_all_key_types():
    # Arrange
    boto3_session = MagicMock()
    client = boto3_session.client.return_value
    paginator = client.get_paginator.return_value
    certificates = [
        {
            "CertificateArn": f"arn:aws:acm:us-east-1:000000000000:certificate/{key_type}",
            "KeyAlgorithm": key_type,
        }
        for key_type in ("RSA_2048", "EC_prime256v1", "RSA_4096")
    ]
    paginator.paginate.return_value = [
        {"CertificateSummaryList": certificates[:1]},
        {"CertificateSummaryList": certificates[1:]},
    ]
    client.describe_certificate.side_effect = [
        {"Certificate": certificate} for certificate in certificates
    ]

    # Act
    result = acm.get_acm_certificates(boto3_session, "us-east-1")

    # Assert
    client.get_paginator.assert_called_once_with("list_certificates")
    paginator.paginate.assert_called_once_with(
        Includes={
            "keyTypes": [
                "RSA_1024",
                "RSA_2048",
                "RSA_3072",
                "RSA_4096",
                "EC_prime256v1",
                "EC_secp384r1",
                "EC_secp521r1",
            ],
        },
    )
    assert result == certificates
    assert client.describe_certificate.call_args_list == [
        call(CertificateArn=certificate["CertificateArn"])
        for certificate in certificates
    ]


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
