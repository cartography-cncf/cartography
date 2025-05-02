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
        "CreatedDate": datetime.datetime(2014, 4, 16, 18, 14, 49, tzinfo=tz.utc),
        "LastRotatedDate": datetime.datetime(2014, 4, 16, 18, 14, 49, tzinfo=tz.utc),
        "LastChangedDate": datetime.datetime(2014, 4, 16, 18, 14, 49, tzinfo=tz.utc),
        "LastAccessedDate": datetime.datetime(2014, 4, 16, 18, 14, 49, tzinfo=tz.utc),
        "PrimaryRegion": "us-west-1",
    },
    {
        "ARN": "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-secret-2-000000",
        "Name": "test-secret-2",
        "Description": "This is another test secret",
        "RotationEnabled": False,
        "CreatedDate": datetime.datetime(2014, 4, 16, 18, 14, 49, tzinfo=tz.utc),
        "LastChangedDate": datetime.datetime(2014, 4, 16, 18, 14, 49, tzinfo=tz.utc),
        "LastAccessedDate": datetime.datetime(2014, 4, 16, 18, 14, 49, tzinfo=tz.utc),
    },
]
