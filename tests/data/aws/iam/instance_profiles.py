import datetime

INSTANCE_PROFILES = [
    {
        "Path": "/",
        "InstanceProfileName": "cartography-service",
        "InstanceProfileId": "AIPA4SD",
        "Arn": "arn:aws:iam::1234:instance-profile/cartography-service",
        "CreateDate": datetime.datetime(2024, 12, 21, 23, 54, 16),
        "Roles": [
            {
                "Path": "/",
                "RoleName": "cartography-service",
                "RoleId": "AROA4",
                "Arn": "arn:aws:iam::1234:role/cartography-service",
                "CreateDate": datetime.datetime(2024, 12, 21, 6, 53, 29),
                "AssumeRolePolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "AWS": "arn:aws:iam:3456:role/test-service",
                            },
                            "Action": "sts:AssumeRole",
                            "Condition": {},
                        },
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "AWS": "arn:aws:iam::1234:root",
                                "Service": "ec2.amazonaws.com",
                            },
                            "Action": "sts:AssumeRole",
                            "Condition": {},
                        },
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "ec2.amazonaws.com",
                            },
                            "Action": "sts:AssumeRole",
                        },
                    ],
                },
            }
        ],
    }
]
