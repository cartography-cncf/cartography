# Create group policy data that matches the groups in LIST_GROUPS
GET_GROUP_INLINE_POLS_SAMPLE = {
    "arn:aws:iam::1234:group/example-group-0": {
        "group_inline_policy": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:PutObject",
                ],
                "Resource": [
                    "arn:aws:s3:::example-bucket",
                    "arn:aws:s3:::example-bucket/*",
                ],
            },
            {
                "Sid": "VisualEditor1",
                "Effect": "Allow",
                "Action": [
                    "ec2:DescribeInstances",
                    "ec2:DescribeSecurityGroups",
                ],
                "Resource": "*",
            },
        ],
    },
    "arn:aws:iam::1234:group/example-group-1": {
        "admin_policy": [
            {
                "Effect": "Allow",
                "Action": "*",
                "Resource": "*",
            },
        ],
    },
}

GET_GROUP_MANAGED_POLICY_DATA = {
    "arn:aws:iam::1234:group/example-group-0": {
        "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket",
                ],
                "Resource": "*",
            },
        ],
        "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess": [
            {
                "Effect": "Allow",
                "Action": [
                    "ec2:Describe*",
                    "elasticloadbalancing:Describe*",
                ],
                "Resource": "*",
            },
        ],
    },
    "arn:aws:iam::1234:group/example-group-1": {
        "arn:aws:iam::aws:policy/AdministratorAccess": [
            {
                "Effect": "Allow",
                "Action": "*",
                "Resource": "*",
            },
        ],
    },
}
