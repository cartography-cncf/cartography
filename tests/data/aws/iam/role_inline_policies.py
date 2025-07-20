# Create inline policy data that matches the roles in ANOTHER_GET_ROLE_LIST_DATASET
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
    "arn:aws:iam::1234:role/ElasticacheAutoscale": {},
    "arn:aws:iam::1234:role/sftp-LambdaExecutionRole-1234": {},
}
