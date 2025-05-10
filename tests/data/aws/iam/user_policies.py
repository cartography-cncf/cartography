from datetime import datetime

GET_USER_LIST_DATA = {
    "Users": [
        {
            "Path": "/",
            "UserName": "user1",
            "UserId": "AIDAXJNIGTSXXX",
            "Arn": "arn:aws:iam::1234:user/user1",
            "CreateDate": datetime(2022, 7, 27, 20, 24, 23),
        },
        {
            "Path": "/",
            "UserName": "user2",
            "UserId": "AIDAXJNIGTSXXY",
            "Arn": "arn:aws:iam::1234:user/user2",
            "CreateDate": datetime(2021, 1, 25, 18, 8, 53),
        },
        {
            "Path": "/",
            "UserName": "user3",
            "UserId": "AIDAXJNIGTSQXYY",
            "Arn": "arn:aws:iam::1234:user/user3",
            "CreateDate": datetime(2020, 3, 23, 20, 26, 23),
        },
    ],
}


GET_USER_MANAGED_POLS_SAMPLE = {
    "arn:aws:iam::1234:user/user1": {
        "arn:aws:iam::1234:policy/user1-user-policy": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "iam:DeleteRolePolicy",
                    "iam:CreateRole",
                    "iam:PutRolePolicy",
                ],
                "Resource": "*",
            },
            {
                "Sid": "VisualEditor1",
                "Effect": "Allow",
                "Action": "iam:PutRolePolicy",
                "Resource": "arn:aws:iam::1234:role/lambda-user1-exec",
            },
        ],
        "arn:aws:iam::aws:policy/AmazonS3FullAccess": [
            {
                "Effect": "Allow",
                "Action": ["s3:*", "s3-object-lambda:*"],
                "Resource": "*",
            },
        ],
        "arn:aws:iam::aws:policy/AWSLambda_FullAccess": [
            {
                "Effect": "Allow",
                "Action": [
                    "cloudformation:DescribeStacks",
                    "cloudformation:ListStackResources",
                    "cloudwatch:ListMetrics",
                    "cloudwatch:GetMetricData",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeVpcs",
                    "kms:ListAliases",
                    "iam:GetPolicy",
                    "iam:GetPolicyVersion",
                    "iam:GetRole",
                    "iam:GetRolePolicy",
                    "iam:ListAttachedRolePolicies",
                    "iam:ListRolePolicies",
                    "iam:ListRoles",
                    "lambda:*",
                    "logs:DescribeLogGroups",
                    "states:DescribeStateMachine",
                    "states:ListStateMachines",
                    "tag:GetResources",
                    "xray:GetTraceSummaries",
                    "xray:BatchGetTraces",
                ],
                "Resource": "*",
            },
            {
                "Effect": "Allow",
                "Action": "iam:PassRole",
                "Resource": "*",
                "Condition": {
                    "StringEquals": {"iam:PassedToService": "lambda.amazonaws.com"},
                },
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:DescribeLogStreams",
                    "logs:GetLogEvents",
                    "logs:FilterLogEvents",
                ],
                "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/*",
            },
        ],
    },
    "arn:aws:iam::1234:user/user2": {},
    "arn:aws:iam::1234:user/user3": {
        "arn:aws:iam::aws:policy/AdministratorAccess": [
            {
                "Effect": "Allow",
                "Action": "*",
                "Resource": "*",
            },
        ],
    },
}


GET_ROLE_LIST_DATA = {
    "Roles": [
        {
            "Path": "/",
            "RoleName": "ServiceRole",
            "RoleId": "AROAJJUSH7VXXX",
            "Arn": "arn:aws:iam::1234:role/ServiceRole",
            "CreateDate": datetime(2018, 8, 2, 23, 4, 13),
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "arn:aws:iam::54321:root"},
                        "Action": "sts:AssumeRole",
                        "Condition": {},
                    },
                ],
            },
            "MaxSessionDuration": 360,
        },
        {
            "Path": "/",
            "RoleName": "cartography-read-only",
            "RoleId": "AROAJGFIQ7EXXY",
            "Arn": "arn:aws:iam::1234:role/cartography-read-only",
            "CreateDate": datetime(2018, 6, 19, 0, 42, 12),
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "arn:aws:iam::54321:root"},
                        "Action": "sts:AssumeRole",
                    },
                ],
            },
            "MaxSessionDuration": 360,
        },
        {
            "Path": "/",
            "RoleName": "admin",
            "RoleId": "AROAJPGNHE3XYY",
            "Arn": "arn:aws:iam::1234:role/admin",
            "CreateDate": datetime(2016, 4, 25, 22, 5, 43),
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "arn:aws:iam::54321:root"},
                        "Action": "sts:AssumeRole",
                        "Condition": {"Bool": {"aws:MultiFactorAuthPresent": "true"}},
                    },
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "arn:aws:iam::98765:root"},
                        "Action": "sts:AssumeRole",
                        "Condition": {"Bool": {"aws:MultiFactorAuthPresent": "true"}},
                    },
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Federated": "arn:aws:iam::1234:saml-provider/Okta",
                        },
                        "Action": "sts:AssumeRoleWithSAML",
                        "Condition": {
                            "StringEquals": {
                                "SAML:aud": "https://signin.aws.amazon.com/saml",
                            },
                        },
                    },
                ],
            },
            "MaxSessionDuration": 144,
        },
    ],
}


GET_ROLE_INLINE_POLS_SAMPLE = {
    "arn:aws:iam::1234:role/ServiceRole": {
        "ServiceRole": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "iam:ListPolicies",
                    "iam:GetAccountSummary",
                    "iam:ListAccountAliases",
                    "iam:GenerateServiceLastAccessedDetails",
                    "iam:ListRoles",
                    "iam:ListUsers",
                    "iam:ListGroups",
                    "iam:GetServiceLastAccessedDetails",
                    "iam:ListRolePolicies",
                ],
                "Resource": "*",
            },
        ],
    },
    "arn:aws:iam::1234:role/cartography-read-only": {},
    "arn:aws:iam::1234:role/admin": {
        "AdministratorAccess": [
            {
                "Effect": "Allow",
                "Action": "*",
                "Resource": "*",
            },
        ],
    },
}
