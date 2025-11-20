from datetime import datetime, timezone

LIST_SERVER_CERTIFICATES = {
    "ServerCertificateMetadataList": [
        {
            "Arn": "arn:aws:iam::000000000000:server-certificate/test-cert-1",
            "ServerCertificateName": "test-cert-1",
            "Path": "/",
            "ServerCertificateId": "ASCAEXAMPLE1",
            "UploadDate": datetime(2023, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        },
        {
            "Arn": "arn:aws:iam::000000000000:server-certificate/test-cert-2",
            "ServerCertificateName": "test-cert-2",
            "Path": "/cloudfront/",
            "ServerCertificateId": "ASCAEXAMPLE2",
            "UploadDate": datetime(2023, 2, 20, 14, 45, 0, tzinfo=timezone.utc),
        },
    ],
}
