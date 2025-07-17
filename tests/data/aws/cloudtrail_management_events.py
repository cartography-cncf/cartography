from datetime import datetime

# =============================================================================
# INTEGRATION TEST MOCK DATA
# =============================================================================
# Mock data for integration tests that work with real Neo4j database
# Each test uses different account IDs and ARNs to prevent data isolation issues

# Test data for basic relationships test
INTEGRATION_TEST_BASIC_ACCOUNT_ID = "123456789012"
INTEGRATION_TEST_BASIC_IAM_USERS = [
    {
        "UserName": "john.doe",
        "UserId": "AIDACKCEVSQ6C2EXAMPLE",
        "Arn": "arn:aws:iam::123456789012:user/john.doe",
        "Path": "/",
        "CreateDate": datetime(2024, 1, 1, 10, 0, 0),
    },
    {
        "UserName": "alice",
        "UserId": "AIDACKCEVSQ6C2ALICE",
        "Arn": "arn:aws:iam::123456789012:user/alice",
        "Path": "/",
        "CreateDate": datetime(2024, 1, 1, 10, 0, 0),
    },
]

INTEGRATION_TEST_BASIC_IAM_ROLES = [
    {
        "RoleName": "ApplicationRole",
        "RoleId": "AROA00000000000000001",
        "Arn": "arn:aws:iam::123456789012:role/ApplicationRole",
        "Path": "/",
        "CreateDate": datetime(2024, 1, 1, 10, 0, 0),
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::123456789012:root"},
                    "Action": "sts:AssumeRole",
                }
            ],
        },
    },
]

# Test data for aggregation test - different account to prevent conflicts
INTEGRATION_TEST_AGGREGATION_ACCOUNT_ID = "111111111111"
INTEGRATION_TEST_AGGREGATION_IAM_USERS = [
    {
        "UserName": "test-user",
        "UserId": "AIDACKCEVSQ6C2TESTUSER",
        "Arn": "arn:aws:iam::111111111111:user/test-user",
        "Path": "/",
        "CreateDate": datetime(2024, 1, 1, 10, 0, 0),
    },
]

INTEGRATION_TEST_AGGREGATION_IAM_ROLES = [
    {
        "RoleName": "TestRole",
        "RoleId": "AROA00000000000000002",
        "Arn": "arn:aws:iam::111111111111:role/TestRole",
        "Path": "/",
        "CreateDate": datetime(2024, 1, 1, 10, 0, 0),
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::111111111111:root"},
                    "Action": "sts:AssumeRole",
                }
            ],
        },
    },
]

# Test data for cross-account test - different account to prevent conflicts
INTEGRATION_TEST_CROSS_ACCOUNT_ID = "222222222222"
INTEGRATION_TEST_CROSS_ACCOUNT_IAM_USERS = [
    {
        "UserName": "cross-user",
        "UserId": "AIDACKCEVSQ6C2CROSSUSER",
        "Arn": "arn:aws:iam::222222222222:user/cross-user",
        "Path": "/",
        "CreateDate": datetime(2024, 1, 1, 10, 0, 0),
    },
]

INTEGRATION_TEST_CROSS_ACCOUNT_IAM_ROLES = [
    {
        "RoleName": "ExternalRole",
        "RoleId": "AROA00000000000000003",
        "Arn": "arn:aws:iam::333333333333:role/ExternalRole",
        "Path": "/",
        "CreateDate": datetime(2024, 1, 1, 10, 0, 0),
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::222222222222:root"},
                    "Action": "sts:AssumeRole",
                }
            ],
        },
    },
]
