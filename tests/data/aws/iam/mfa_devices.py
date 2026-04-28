import datetime

LIST_MFA_DEVICES = [
    {
        "UserName": "user-0",
        "UserArn": "arn:aws:iam::000000000000:user/user-0",
        "SerialNumber": "arn:aws:iam::000000000000:mfa/user-0",
        "EnableDate": datetime.datetime(2024, 1, 15, 10, 30, 0),
    },
    {
        "UserName": "user-0",  # user-0 has 2 MFA devices
        "UserArn": "arn:aws:iam::000000000000:user/user-0",
        "SerialNumber": "arn:aws:iam::000000000000:mfa/user-0-backup",
        "EnableDate": datetime.datetime(2024, 2, 20, 14, 45, 0),
    },
    {
        "UserName": "user-1",
        "UserArn": "arn:aws:iam::000000000000:user/user-1",
        "SerialNumber": "arn:aws:iam::000000000000:mfa/user-1",
        "EnableDate": datetime.datetime(2023, 12, 1, 9, 0, 0),
    },
]
