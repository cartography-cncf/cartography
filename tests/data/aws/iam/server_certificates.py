import datetime

LIST_SERVER_CERTIFICATES_RESPONSE = {
    "ServerCertificateMetadataList": [
        {
            "Path": "/cloudfront/",
            "ServerCertificateName": "test-cert",
            "ServerCertificateId": "ASCATEST",
            "Arn": "arn:aws:iam::123456789012:server-certificate/cloudfront/test-cert",
            "UploadDate": datetime.datetime(2023, 1, 1, 0, 0, 0),
            "Expiration": datetime.datetime(2024, 1, 1, 0, 0, 0),
        }
    ]
}
