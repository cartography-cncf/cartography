from datetime import datetime

# Sample access key data for testing
GET_ACCOUNT_ACCESS_KEY_DATA = {
    "AccessKeyMetadata": [
        {
            "UserName": "user1",
            "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
            "Status": "Active",
            "CreateDate": datetime(2022, 7, 27, 20, 24, 23),
            "LastUsedDate": datetime(2023, 1, 15, 10, 30, 0),
            "LastUsedService": "s3",
            "LastUsedRegion": "us-east-1",
        },
        {
            "UserName": "user1",
            "AccessKeyId": "AKIAI44QH8DHBEXAMPLE",
            "Status": "Inactive",
            "CreateDate": datetime(2022, 6, 15, 14, 20, 10),
            "LastUsedDate": datetime(2022, 12, 20, 16, 45, 30),
            "LastUsedService": "ec2",
            "LastUsedRegion": "us-west-2",
        },
        {
            "UserName": "user2",
            "AccessKeyId": "AKIAJQ5CMEXAMPLE",
            "Status": "Active",
            "CreateDate": datetime(2021, 1, 25, 18, 8, 53),
            "LastUsedDate": datetime(2023, 2, 10, 9, 15, 0),
            "LastUsedService": "lambda",
            "LastUsedRegion": "us-east-1",
        },
        {
            "UserName": "user3",
            "AccessKeyId": "AKIAEXAMPLE123",
            "Status": "Active",
            "CreateDate": datetime(2020, 3, 23, 20, 26, 23),
            "LastUsedDate": None,  # Never used
            "LastUsedService": "",
            "LastUsedRegion": "",
        },
    ]
}

# Sample user access keys data (mapping user ARN to access key list)
GET_USER_ACCESS_KEYS_DATA = {
    "arn:aws:iam::1234:user/user1": [
        {
            "UserName": "user1",
            "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
            "Status": "Active",
            "CreateDate": datetime(2022, 7, 27, 20, 24, 23),
            "LastUsedDate": datetime(2023, 1, 15, 10, 30, 0),
            "LastUsedService": "s3",
            "LastUsedRegion": "us-east-1",
        },
        {
            "UserName": "user1",
            "AccessKeyId": "AKIAI44QH8DHBEXAMPLE",
            "Status": "Inactive",
            "CreateDate": datetime(2022, 6, 15, 14, 20, 10),
            "LastUsedDate": datetime(2022, 12, 20, 16, 45, 30),
            "LastUsedService": "ec2",
            "LastUsedRegion": "us-west-2",
        },
    ],
    "arn:aws:iam::1234:user/user2": [
        {
            "UserName": "user2",
            "AccessKeyId": "AKIAJQ5CMEXAMPLE",
            "Status": "Active",
            "CreateDate": datetime(2021, 1, 25, 18, 8, 53),
            "LastUsedDate": datetime(2023, 2, 10, 9, 15, 0),
            "LastUsedService": "lambda",
            "LastUsedRegion": "us-east-1",
        },
    ],
    "arn:aws:iam::1234:user/user3": [
        {
            "UserName": "user3",
            "AccessKeyId": "AKIAEXAMPLE123",
            "Status": "Active",
            "CreateDate": datetime(2020, 3, 23, 20, 26, 23),
            "LastUsedDate": None,  # Never used
            "LastUsedService": "",
            "LastUsedRegion": "",
        },
    ],
}
