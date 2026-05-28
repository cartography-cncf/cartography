from datetime import datetime

GET_USER_SERVICE_SPECIFIC_CREDENTIALS_DATA = {
    "arn:aws:iam::1234:user/user1": [
        {
            "UserName": "user1",
            "Status": "Active",
            "ServiceUserName": "AKIAUSER1AT1670000000000",
            "CreateDate": datetime(2024, 1, 12, 18, 5, 0),
            "ServiceSpecificCredentialId": "ANPAEXAMPLEUSER1A",
            "ServiceName": "codecommit.amazonaws.com",
        },
        {
            "UserName": "user1",
            "Status": "Inactive",
            "ServiceUserName": "AIDAUSER1AT1670000000001",
            "CreateDate": datetime(2024, 4, 3, 9, 30, 0),
            "ServiceSpecificCredentialId": "ANPAEXAMPLEUSER1B",
            "ServiceName": "bedrock.amazonaws.com",
        },
    ],
    "arn:aws:iam::1234:user/user2": [
        {
            "UserName": "user2",
            "Status": "Active",
            "ServiceUserName": "AKIAUSER2AT1670000000000",
            "CreateDate": datetime(2025, 2, 6, 11, 45, 0),
            "ServiceSpecificCredentialId": "ANPAEXAMPLEUSER2A",
            "ServiceName": "codecommit.amazonaws.com",
        },
    ],
    "arn:aws:iam::1234:user/user3": [],
}
