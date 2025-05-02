from datetime import datetime

ANOTHER_GET_ROLE_LIST_DATASET = {
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
            "MaxSessionDuration": 3600,
        },
        {
            "Path": "/",
            "RoleName": "ElasticacheAutoscale",
            "RoleId": "AROAXJNIGTSXXY",
            "Arn": "arn:aws:iam::1234:role/ElasticacheAutoscale",
            "CreateDate": datetime(2019, 8, 13, 20, 10, 58),
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    },
                ],
            },
            "Description": "Allows Lambda functions to call AWS services on your behalf.",
            "MaxSessionDuration": 3600,
        },
        {
            "Path": "/",
            "RoleName": "sftp-LambdaExecutionRole-1234",
            "RoleId": "AROAXJNIGTSXYY",
            "Arn": "arn:aws:iam::1234:role/sftp-LambdaExecutionRole-1234",
            "CreateDate": datetime(2019, 9, 18, 5, 1, 21),
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    },
                ],
            },
            "Description": "",
            "MaxSessionDuration": 3600,
        },
    ],
}

GET_ROLE_MANAGED_POLICY_DATA = {
    "arn:aws:iam::1234:role/ServiceRole": {},
    "arn:aws:iam::1234:role/ElasticacheAutoscale": {
        "arn:aws:iam::1234:policy/AWSLambdaBasicExecutionRole-autoscaleElasticache": [
            {
                "Effect": "Allow",
                "Action": "logs:CreateLogGroup",
                "Resource": "arn:aws:logs:us-east-1:1234:*",
            },
            {
                "Effect": "Allow",
                "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
                "Resource": ["arn:aws:logs:us-east-1:1234:log-group:/aws/lambda/*:*"],
            },
        ],
        "arn:aws:iam::aws:policy/AWSLambdaFullAccess": [
            {
                "Effect": "Allow",
                "Action": [
                    "cloudformation:DescribeChangeSet",
                    "cloudformation:DescribeStackResources",
                    "cloudformation:DescribeStacks",
                    "cloudformation:GetTemplate",
                    "cloudformation:ListStackResources",
                    "cloudwatch:*",
                    "cognito-identity:ListIdentityPools",
                    "cognito-sync:GetCognitoEvents",
                    "cognito-sync:SetCognitoEvents",
                    "dynamodb:*",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeVpcs",
                    "events:*",
                    "iam:GetPolicy",
                    "iam:GetPolicyVersion",
                    "iam:GetRole",
                    "iam:GetRolePolicy",
                    "iam:ListAttachedRolePolicies",
                    "iam:ListRolePolicies",
                    "iam:ListRoles",
                    "iam:PassRole",
                    "iot:AttachPrincipalPolicy",
                    "iot:AttachThingPrincipal",
                    "iot:CreateKeysAndCertificate",
                    "iot:CreatePolicy",
                    "iot:CreateThing",
                    "iot:CreateTopicRule",
                    "iot:DescribeEndpoint",
                    "iot:GetTopicRule",
                    "iot:ListPolicies",
                    "iot:ListThings",
                    "iot:ListTopicRules",
                    "iot:ReplaceTopicRule",
                    "kinesis:DescribeStream",
                    "kinesis:ListStreams",
                    "kinesis:PutRecord",
                    "kms:ListAliases",
                    "lambda:*",
                    "logs:*",
                    "s3:*",
                    "sns:ListSubscriptions",
                    "sns:ListSubscriptionsByTopic",
                    "sns:ListTopics",
                    "sns:Publish",
                    "sns:Subscribe",
                    "sns:Unsubscribe",
                    "sqs:ListQueues",
                    "sqs:SendMessage",
                    "tag:GetResources",
                    "xray:PutTelemetryRecords",
                    "xray:PutTraceSegments",
                ],
                "Resource": "*",
            },
        ],
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                "Resource": "*",
            },
        ],
        "arn:aws:iam::aws:policy/service-role/AWSLambdaRole": [
            {
                "Effect": "Allow",
                "Action": ["lambda:InvokeFunction"],
                "Resource": ["*"],
            },
        ],
        "arn:aws:iam::aws:policy/AmazonElastiCacheFullAccess": [
            {
                "Action": "elasticache:*",
                "Effect": "Allow",
                "Resource": "*",
            },
            {
                "Action": "iam:CreateServiceLinkedRole",
                "Effect": "Allow",
                "Resource": "arn:aws:iam::*:role/aws-service-role/elasticache.amazonaws.com"
                "/AWSServiceRoleForElastiCache",
                "Condition": {
                    "StringLike": {"iam:AWSServiceName": "elasticache.amazonaws.com"},
                },
            },
        ],
    },
    "arn:aws:iam::1234:role/sftp-LambdaExecutionRole-1234": {
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                "Resource": "*",
            },
        ],
    },
}
