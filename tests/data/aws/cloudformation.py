TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789
TEST_REGION = "us-east-1"

CLOUDFORMATION_STACKS = [
    {
        "StackId": f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/test-stack/12345678-90ab-cdef-1234-567890abcdef",
        "StackName": "test-stack",
        "Description": "Test stack for CloudFormation ingestion",
        "CreationTime": "2025-01-01T12:00:00Z",
        "LastUpdatedTime": "2025-01-02T12:00:00Z",
        "StackStatus": "CREATE_COMPLETE",
        "StackStatusReason": "User Initiated",
        "DisableRollback": False,
        "TimeoutInMinutes": 10,
        "NotificationARNs": [
            f"arn:aws:sns:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack-notify"
        ],
        "Capabilities": ["CAPABILITY_IAM"],
        "Tags": [{"Key": "env", "Value": "test"}],
        "RoleARN": f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/CloudFormationExecutionRole",
    },
    {
        "StackId": f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/parent-stack/abcdef12-3456-7890-abcd-ef1234567890",
        "StackName": "parent-stack",
        "Description": "Parent stack",
        "CreationTime": "2025-01-03T12:00:00Z",
        "StackStatus": "UPDATE_COMPLETE",
        "ParentId": f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/root-stack/00000000-0000-0000-0000-000000000000",
        "RootId": f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/root-stack/00000000-0000-0000-0000-000000000000",
        "Capabilities": ["CAPABILITY_NAMED_IAM"],
        "Tags": [{"Key": "env", "Value": "prod"}],
    },
]
