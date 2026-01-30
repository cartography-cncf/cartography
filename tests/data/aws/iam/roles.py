import datetime

ROLES = {
    "Roles": [
        {
            "Path": "/aws-reserved/sso.amazonaws.com/",
            "RoleName": "AWSReservedSSO_AdministratorAccess_1345",
            "RoleId": "AROA",
            "Arn": "arn:aws:iam::1234:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_AdministratorAccess_1345",
            "CreateDate": datetime.datetime(2024, 12, 18, 22, 12, 27),
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Federated": "arn:aws:iam::1234:saml-provider/AWSSSO_89d_DO_NOT_DELETE",
                        },
                        "Action": [
                            "sts:AssumeRoleWithSAML",
                            "sts:TagSession",
                        ],
                        "Condition": {
                            "StringEquals": {
                                "SAML:aud": "https://signin.aws.amazon.com/saml",
                            },
                        },
                    },
                ],
            },
            "Description": "Provides full access to AWS services and resources.",
            "MaxSessionDuration": 43200,
        },
        {
            "Path": "/",
            "RoleName": "cartography-read-only",
            "RoleId": "AROA4",
            "Arn": "arn:aws:iam::1234:role/cartography-read-only",
            "CreateDate": datetime.datetime(2024, 12, 22, 3, 34, 47),
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "arn:aws:iam::1234:role/cartography-service",
                        },
                        "Action": "sts:AssumeRole",
                        "Condition": {},
                    },
                ],
            },
            "Description": "Read-only access for cartography",
            "MaxSessionDuration": 3600,
        },
        {
            "Path": "/",
            "RoleName": "cartography-service",
            "RoleId": "AROA4S",
            "Arn": "arn:aws:iam::1234:role/cartography-service",
            "CreateDate": datetime.datetime(2024, 12, 21, 6, 53, 29),
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "arn:aws:iam::3456:role/test-service",
                        },
                        "Action": "sts:AssumeRole",
                        "Condition": {},
                    },
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "ec2.amazonaws.com",
                            "AWS": "arn:aws:iam::1234:root",
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
            "Description": "cartography service role for the management account",
            "MaxSessionDuration": 3600,
        },
    ],
}
