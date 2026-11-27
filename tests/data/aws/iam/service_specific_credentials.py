import datetime

LIST_SERVICE_SPECIFIC_CREDENTIALS = [
    {
        "UserName": "user-0",
        "UserArn": "arn:aws:iam::000000000000:user/user-0",
        "ServiceName": "bedrock.amazonaws.com",
        "ServiceCredentialAlias": "user-0-at-000000000000",
        "ServiceSpecificCredentialId": "ACCA00000000000000001",
        "Status": "Active",
        "CreateDate": datetime.datetime(2025, 7, 1, 12, 0, 0),
        "ExpirationDate": datetime.datetime(2025, 10, 1, 12, 0, 0),
    },
    {
        "UserName": "user-1",
        "UserArn": "arn:aws:iam::000000000000:user/user-1",
        "ServiceName": "codecommit.amazonaws.com",
        "ServiceUserName": "user-1-at-000000000000",
        "ServiceSpecificCredentialId": "ACCA00000000000000002",
        "Status": "Inactive",
        "CreateDate": datetime.datetime(2024, 3, 5, 8, 0, 0),
    },
]
