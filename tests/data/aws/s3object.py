import datetime
from datetime import timezone
from typing import Dict
from typing import List

LIST_S3_OBJECTS = [
    {
        "Key": "documents/report.pdf",
        "ARN": "arn:aws:s3:::test-bucket/documents/report.pdf",
        "LastModified": datetime.datetime(2025, 5, 20, 10, 0, 0, tzinfo=timezone.utc),
        "ETag": "abc123",
        "Size": 1024000,
        "StorageClass": "STANDARD",
    },
    {
        "Key": "images/logo.png",
        "ARN": "arn:aws:s3:::test-bucket/images/logo.png",
        "LastModified": datetime.datetime(2025, 5, 21, 14, 30, 0, tzinfo=timezone.utc),
        "ETag": "def456",
        "Size": 50000,
        "StorageClass": "STANDARD_IA",
        "Owner": {"DisplayName": "test-owner", "ID": "owner-id-123"},
    },
    {
        "Key": "archive/old-data.zip",
        "ARN": "arn:aws:s3:::test-bucket/archive/old-data.zip",
        "LastModified": datetime.datetime(2025, 5, 15, 8, 0, 0, tzinfo=timezone.utc),
        "ETag": "ghi789",
        "Size": 5000000,
        "StorageClass": "GLACIER",
        "RestoreStatus": {
            "IsRestoreInProgress": True,
            "RestoreExpiryDate": datetime.datetime(
                2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc
            ),
        },
    },
    {
        "Key": "deleted/file.txt",
        "ARN": "arn:aws:s3:::test-bucket/deleted/file.txt",
        "LastModified": datetime.datetime(2025, 5, 22, 9, 0, 0, tzinfo=timezone.utc),
        "ETag": "jkl012",
        "Size": 0,
        "StorageClass": "STANDARD",
    },
]

EMPTY_BUCKET_OBJECTS: List[Dict] = []

SINGLE_OBJECT_WITH_OWNER = [
    {
        "Key": "images/logo.png",
        "ARN": "arn:aws:s3:::test-bucket/images/logo.png",
        "LastModified": datetime.datetime(2025, 5, 21, 14, 30, 0, tzinfo=timezone.utc),
        "ETag": "def456",
        "Size": 50000,
        "StorageClass": "STANDARD_IA",
        "Owner": {"DisplayName": "test-owner", "ID": "owner-id-123"},
    }
]

SINGLE_GLACIER_OBJECT = [
    {
        "Key": "archive/old-data.zip",
        "ARN": "arn:aws:s3:::test-bucket/archive/old-data.zip",
        "LastModified": datetime.datetime(2025, 5, 15, 8, 0, 0, tzinfo=timezone.utc),
        "ETag": "ghi789",
        "Size": 5000000,
        "StorageClass": "GLACIER",
        "RestoreStatus": {
            "IsRestoreInProgress": True,
            "RestoreExpiryDate": datetime.datetime(
                2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc
            ),
        },
    }
]
