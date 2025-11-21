LIST_CERTIFICATES = {
    "CertificateSummaryList": [
        {
            "CertificateArn": "arn:aws:acm:us-east-1:000000000000:certificate/test-cert",
            "DomainName": "example.com",
        }
    ]
}

DESCRIBE_CERTIFICATE = {
    "Certificate": {
        "CertificateArn": "arn:aws:acm:us-east-1:000000000000:certificate/test-cert",
        "DomainName": "example.com",
        "InUseBy": [
            "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/test-lb/abcd/efgh"
        ],
        "Type": "IMPORTED",
        "Status": "ISSUED",
        "KeyAlgorithm": "RSA_2048",
        "SignatureAlgorithm": "SHA256WITHRSA",
        "NotBefore": "2024-01-01T00:00:00Z",
        "NotAfter": "2025-01-01T00:00:00Z",
    }
}
