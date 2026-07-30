import datetime

LIST_USERS = {
    "Users": [
        {
            "UserName": "example-user-0",
            "PasswordLastUsed": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "UserId": "AIDA00000000000000000",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:user/example-user-0",
        },
        {
            "UserName": "example-user-1",
            "PasswordLastUsed": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "UserId": "AIDA00000000000000001",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:user/example-user-1",
        },
    ],
}


LIST_GROUPS = {
    "Groups": [
        {
            "Path": "/",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "GroupId": "AGPA000000000000000000",
            "Arn": "arn:aws:iam::000000000000:group/example-group-0",
            "GroupName": "example-group-0",
        },
        {
            "Path": "/",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "GroupId": "AGPA000000000000000001",
            "Arn": "arn:aws:iam::000000000000:group/example-group-1",
            "GroupName": "example-group-1",
        },
    ],
}

LIST_GROUPS_SAMPLE = {
    "Groups": [
        {
            "Path": "/",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "GroupId": "AGPA000000000000000000",
            "Arn": "arn:aws:iam::1234:group/example-group-0",
            "GroupName": "example-group-0",
        },
        {
            "Path": "/",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "GroupId": "AGPA000000000000000001",
            "Arn": "arn:aws:iam::1234:group/example-group-1",
            "GroupName": "example-group-1",
        },
    ],
}

# Group membership data - maps group ARN to list of user ARNs
GET_GROUP_MEMBERSHIPS_DATA = {
    "arn:aws:iam::1234:group/example-group-0": [
        "arn:aws:iam::1234:user/user1",
        "arn:aws:iam::1234:user/user2",
    ],
    "arn:aws:iam::1234:group/example-group-1": [
        "arn:aws:iam::1234:user/user3",
    ],
}

INLINE_POLICY_STATEMENTS = [
    {
        "id": "allow_all_policy",
        "Action": [
            "*",
        ],
        "Resource": [
            "*",
        ],
        "Effect": "Allow",
    },
]

LIST_ROLES = {
    "Roles": [
        {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "arn:aws:iam::000000000000:root",
                        },
                    },
                ],
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000000",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "RoleName": "example-role-0",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/example-role-0",
        },
        {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "arn:aws:iam::000000000000:role/example-role-0",
                        },
                    },
                ],
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000001",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "RoleName": "example-role-1",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/example-role-1",
        },
        {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "ec2.amazonaws.com",
                        },
                    },
                ],
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000002",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "RoleName": "example-role-2",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/example-role-2",
        },
        {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRoleWithSAML",
                        "Effect": "Allow",
                        "Principal": {
                            "Federated": "arn:aws:iam::000000000000:saml-provider/ADFS",
                        },
                        "Condition": {
                            "StringEquals": {
                                "SAML:aud": "https://signin.aws.amazon.com/saml",
                            },
                        },
                    },
                ],
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000003",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "RoleName": "example-role-3",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/example-role-3",
        },
    ],
}

GITHUB_OIDC_PROVIDER_ARN = (
    "arn:aws:iam::000000000000:oidc-provider/token.actions.githubusercontent.com"
)

# Roles trusting the GitHub Actions OIDC provider. The first two are identical apart from
# the sub condition that scopes them, which is the distinction the trust edge has to
# preserve. The third trusts the same provider from two statements, one of which is
# unconditional.
LIST_ROLES_GITHUB_OIDC = {
    "Roles": [
        {
            # Pinned to one branch of one repo.
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRoleWithWebIdentity",
                        "Effect": "Allow",
                        "Principal": {"Federated": GITHUB_OIDC_PROVIDER_ARN},
                        "Condition": {
                            "StringEquals": {
                                "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                                "token.actions.githubusercontent.com:sub": "repo:octo-org/octo-repo:ref:refs/heads/main",
                            },
                        },
                    },
                ],
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000010",
            "CreateDate": datetime.datetime(2026, 1, 1, 0, 0, 1),
            "RoleName": "gha-pinned",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/gha-pinned",
        },
        {
            # Org-wide. IAM `*` is not path-aware, so it spans both `/` and `:`: every
            # repo under octo-org, every ref, and the `pull_request` subject match.
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRoleWithWebIdentity",
                        "Effect": "Allow",
                        "Principal": {"Federated": GITHUB_OIDC_PROVIDER_ARN},
                        "Condition": {
                            "StringLike": {
                                "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                                "token.actions.githubusercontent.com:sub": "repo:octo-org/*",
                            },
                        },
                    },
                ],
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000011",
            "CreateDate": datetime.datetime(2026, 1, 1, 0, 0, 1),
            "RoleName": "gha-org-wide",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/gha-org-wide",
        },
        {
            # Two statements trusting the same provider. The unconditional one wins, so
            # the aggregated edge is not conditional.
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRoleWithWebIdentity",
                        "Effect": "Allow",
                        "Principal": {"Federated": GITHUB_OIDC_PROVIDER_ARN},
                        "Condition": {
                            "StringEquals": {
                                "token.actions.githubusercontent.com:sub": "repo:octo-org/octo-repo:ref:refs/heads/main",
                            },
                        },
                    },
                    {
                        "Action": "sts:AssumeRoleWithWebIdentity",
                        "Effect": "Allow",
                        "Principal": {"Federated": GITHUB_OIDC_PROVIDER_ARN},
                    },
                ],
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000012",
            "CreateDate": datetime.datetime(2026, 1, 1, 0, 0, 1),
            "RoleName": "gha-mixed",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/gha-mixed",
        },
    ],
}

LIST_SAML_PROVIDERS = {
    "SAMLProviderList": [
        {
            "Arn": "arn:aws:iam::000000000000:saml-provider/ADFS",
            "Name": "ADFS",
            "ValidUntil": datetime.datetime(2025, 12, 31, 23, 59, 59),
            "CreateDate": datetime.datetime(2020, 1, 1, 0, 0, 0),
        },
        {
            "Arn": "arn:aws:iam::000000000000:saml-provider/Okta",
            "Name": "Okta",
            "ValidUntil": datetime.datetime(2026, 1, 1, 0, 0, 0),
            "CreateDate": datetime.datetime(2021, 6, 15, 12, 0, 0),
        },
    ]
}

INSTACE = {
    "Roles": [
        {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "arn:aws:iam::000000000000:role/SERVICE_NAME_2",
                        },
                    },
                ],
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000004",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "RoleName": "SERVICE_NAME_2",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/SERVICE_NAME_2",
        },
        {
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "arn:aws:iam::000000000000:role/ANOTHER_SERVICE_NAME",
                        },
                    },
                ],
            },
            "MaxSessionDuration": 3600,
            "RoleId": "AROA00000000000000006",
            "CreateDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "RoleName": "ANOTHER_SERVICE_NAME",
            "Path": "/",
            "Arn": "arn:aws:iam::000000000000:role/ANOTHER_SERVICE_NAME",
        },
    ],
}


SERVICE_LAST_ACCESSED_DETAILS = {
    "JobStatus": "COMPLETED",
    "JobCreationDate": datetime.datetime(2019, 1, 1, 0, 0, 1),
    "JobCompletionDate": datetime.datetime(2019, 1, 1, 0, 0, 2),
    "ServicesLastAccessed": [
        {
            "ServiceName": "Amazon S3",
            "ServiceNamespace": "s3",
            "LastAuthenticated": datetime.datetime(2019, 1, 1, 0, 0, 1),
            "LastAuthenticatedEntity": "user/example-user-0",
            "LastAuthenticatedRegion": "us-east-1",
            "TotalAuthenticatedEntities": 1,
        },
        {
            "ServiceName": "Amazon EC2",
            "ServiceNamespace": "ec2",
            "LastAuthenticated": datetime.datetime(2019, 1, 2, 0, 0, 1),
            "LastAuthenticatedEntity": "role/example-role-0",
            "LastAuthenticatedRegion": "us-west-2",
            "TotalAuthenticatedEntities": 2,
        },
    ],
}
