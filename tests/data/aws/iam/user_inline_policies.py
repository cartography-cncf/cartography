# Create user inline policy data
GET_USER_INLINE_POLS_SAMPLE = {
    "arn:aws:iam::1234:user/user1": {
        "user1_inline_policy": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:DeleteItem",
                ],
                "Resource": "arn:aws:dynamodb:us-east-1:1234:table/user1-table",
            },
            {
                "Sid": "VisualEditor1",
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                ],
                "Resource": "arn:aws:s3:::user1-bucket/*",
            },
        ],
    },
    "arn:aws:iam::1234:user/user2": {
        "user2_admin_policy": [
            {
                "Effect": "Allow",
                "Action": "*",
                "Resource": "*",
            },
        ],
    },
    "arn:aws:iam::1234:user/user3": {},
}
