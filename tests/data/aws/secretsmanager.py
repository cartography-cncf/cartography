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

# Raw AWS API response data for transform_secrets function testing (INPUT to transform_secrets)
SECRETS_RAW_DATA = [
    {
        "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret-with-rotation-AbCdEf",
        "Name": "test-secret-with-rotation",
        "Description": "A test secret with rotation enabled",
        "RotationEnabled": True,
        "RotationRules": {"AutomaticallyAfterDays": 90},  # This should be flattened
        "RotationLambdaARN": "arn:aws:lambda:us-east-1:123456789012:function:rotate-secret",
        "KmsKeyId": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
        "CreatedDate": datetime.datetime(
            2024, 1, 15, 10, 30, 0, tzinfo=tz.utc
        ),  # Should become epoch
        "LastRotatedDate": datetime.datetime(
            2024, 4, 15, 10, 30, 0, tzinfo=tz.utc
        ),  # Should become epoch
        "LastChangedDate": datetime.datetime(
            2024, 5, 1, 14, 45, 30, tzinfo=tz.utc
        ),  # Should become epoch
        "LastAccessedDate": datetime.datetime(
            2024, 5, 10, 16, 20, 15, tzinfo=tz.utc
        ),  # Should become epoch
        "PrimaryRegion": "us-west-2",
        "OwningService": "lambda",
    },
    {
        "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret-no-rotation-GhIjKl",
        "Name": "test-secret-no-rotation",
        "Description": "A test secret without rotation",
        "RotationEnabled": False,
        # No RotationRules - should not have flattened property
        "KmsKeyId": "arn:aws:kms:us-east-1:123456789012:key/87654321-4321-4321-4321-210987654321",
        "CreatedDate": datetime.datetime(
            2024, 2, 20, 9, 15, 0, tzinfo=tz.utc
        ),  # Should become epoch
        "LastChangedDate": datetime.datetime(
            2024, 3, 10, 11, 30, 45, tzinfo=tz.utc
        ),  # Should become epoch
        "LastAccessedDate": datetime.datetime(
            2024, 5, 8, 8, 45, 0, tzinfo=tz.utc
        ),  # Should become epoch
    },
    {
        "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test-secret-minimal-MnOpQr",
        "Name": "test-secret-minimal",
        "RotationEnabled": False,
        "CreatedDate": datetime.datetime(
            2024, 3, 1, 12, 0, 0, tzinfo=tz.utc
        ),  # Should become epoch
        # Minimal data - many optional fields missing
    },
]
