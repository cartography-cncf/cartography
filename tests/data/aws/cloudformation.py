TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789

DESCRIBE_STACKS = [
    {
        "StackId": f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/test-stack-1/11111111-1111-1111-1111-111111111111",
        "StackName": "test-stack-1",
        "Description": "Test CloudFormation stack for cartography",
        "CreationTime": "2024-01-01T12:00:00Z",
        "LastUpdatedTime": "2024-01-02T12:00:00Z",
        "StackStatus": "CREATE_COMPLETE",
        "DisableRollback": False,
        "RoleARN": f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/CloudFormationExecutionRole",
        "Tags": [
            {"Key": "Environment", "Value": "test"},
            {"Key": "Project", "Value": "cartography"},
        ],
        "RollbackConfiguration": {
            "RollbackTriggers": [],
        },
        "DriftInformation": {
            "StackDriftStatus": "NOT_CHECKED",
        },
    },
    {
        "StackId": f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/test-stack-2/22222222-2222-2222-2222-222222222222",
        "StackName": "test-stack-2",
        "Description": "Second test stack",
        "CreationTime": "2024-01-03T12:00:00Z",
        "StackStatus": "UPDATE_COMPLETE",
        "StackStatusReason": "User initiated update",
        "DisableRollback": True,
        "ParentId": f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/parent-stack/00000000-0000-0000-0000-000000000000",
        "RootId": f"arn:aws:cloudformation:{TEST_REGION}:{TEST_ACCOUNT_ID}:stack/root-stack/00000000-0000-0000-0000-000000000000",
        "Tags": [],
    },
]
