import datetime
from datetime import timezone as tz

LIST_SECRETS = [
    {
        "ARN": "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000",
        "Name": "test-secret-1",
        "Description": "This is a test secret",
        "RotationEnabled": True,
        "RotationRules": {"AutomaticallyAfterDays": 90},
        "RotationLambdaARN": "arn:aws:lambda:us-east-1:000000000000:function:test-secret-rotate",
        "KmsKeyId": "arn:aws:kms:us-east-1:000000000000:key/00000000-0000-0000-0000-000000000000",
        "CreatedDate": datetime.datetime(2024, 12, 15, 10, 30, 0, tzinfo=tz.utc),
        "LastRotatedDate": datetime.datetime(2025, 3, 15, 10, 30, 0, tzinfo=tz.utc),
        "LastChangedDate": datetime.datetime(2025, 4, 20, 14, 45, 30, tzinfo=tz.utc),
        "LastAccessedDate": datetime.datetime(2025, 5, 20, 16, 20, 15, tzinfo=tz.utc),
        "PrimaryRegion": "us-west-1",
    },
    {
        "ARN": "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-2-000000",
        "Name": "test-secret-2",
        "Description": "This is another test secret",
        "RotationEnabled": False,
        "CreatedDate": datetime.datetime(2024, 10, 5, 9, 15, 0, tzinfo=tz.utc),
        "LastChangedDate": datetime.datetime(2025, 1, 10, 11, 30, 45, tzinfo=tz.utc),
        "LastAccessedDate": datetime.datetime(2025, 5, 18, 8, 45, 0, tzinfo=tz.utc),
    },
]

LIST_SECRET_VERSIONS = [
    {
        "ARN": "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000:version:00000000-0000-0000-0000-000000000000",
        "SecretId": "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000",
        "VersionId": "00000000-0000-0000-0000-000000000000",
        "VersionStages": ["AWSCURRENT"],
        "CreatedDate": datetime.datetime(2025, 4, 20, 14, 45, 30, tzinfo=tz.utc),
        "KmsKeyId": "arn:aws:kms:us-east-1:000000000000:key/00000000-0000-0000-0000-000000000000",
    },
    {
        "ARN": "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000:version:11111111-1111-1111-1111-111111111111",
        "SecretId": "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-1-000000",
        "VersionId": "11111111-1111-1111-1111-111111111111",
        "VersionStages": ["AWSPREVIOUS"],
        "CreatedDate": datetime.datetime(2025, 3, 15, 10, 30, 0, tzinfo=tz.utc),
        "KmsKeyId": "arn:aws:kms:us-east-1:000000000000:key/00000000-0000-0000-0000-000000000000",
    },
]
