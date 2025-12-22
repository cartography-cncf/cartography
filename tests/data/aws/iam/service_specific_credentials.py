from datetime import datetime


GET_USER_SERVICE_SPECIFIC_CREDENTIALS_DATA = {
    "ServiceSpecificCredentials": [
        {
            "ServiceSpecificCredentialId": "AIDAIOSFODNN7EXAMPLE",
            "ServiceName": "bedrock.amazonaws.com",
            "ServiceUserName": "bedrock-user",
            "Status": "Active",
            "CreateDate": datetime(2023, 7, 27, 20, 24, 23),
        },
        {
            "ServiceSpecificCredentialId": "AIDAI44QH8DHBEXAMPLE",
            "ServiceName": "codecommit.amazonaws.com",
            "ServiceUserName": "codecommit-user",
            "Status": "Inactive",
            "CreateDate": datetime(2023, 6, 15, 14, 20, 10),
        },
    ]
}


GET_USER_SERVICE_SPECIFIC_CREDENTIALS_DATA_MAPPED = {
    "arn:aws:iam::1234:user/user1": [
        {
            "ServiceSpecificCredentialId": "AIDAIOSFODNN7EXAMPLE",
            "ServiceName": "bedrock.amazonaws.com",
            "ServiceUserName": "bedrock-user",
            "Status": "Active",
            "CreateDate": datetime(2023, 7, 27, 20, 24, 23),
        },
        {
            "ServiceSpecificCredentialId": "AIDAI44QH8DHBEXAMPLE",
            "ServiceName": "codecommit.amazonaws.com",
            "ServiceUserName": "codecommit-user",
            "Status": "Inactive",
            "CreateDate": datetime(2023, 6, 15, 14, 20, 10),
        },
    ],
    "arn:aws:iam::1234:user/user2": [
        {
            "ServiceSpecificCredentialId": "AIDAJQ5CMEXAMPLE",
            "ServiceName": "bedrock.amazonaws.com",
            "ServiceUserName": "bedrock-user-2",
            "Status": "Active",
            "CreateDate": datetime(2023, 1, 25, 18, 8, 53),
        },
    ],
    "arn:aws:iam::1234:user/user3": [],
}
