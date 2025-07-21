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
    {
        "RoleName": "SAMLRole",
        "RoleId": "AROA00000000000000002",
        "Arn": "arn:aws:iam::123456789012:role/SAMLRole",
        "Path": "/",
        "CreateDate": datetime(2024, 1, 1, 10, 0, 0),
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": "arn:aws:iam::123456789012:saml-provider/ExampleProvider"
                    },
                    "Action": "sts:AssumeRoleWithSAML",
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

# Test data for SSO users for SAML tests
TEST_SSO_USERS = [
    {
        "UserName": "admin@example.com",
        "UserId": "admin-user-id-1",
        "ExternalIds": [
            {
                "Issuer": "https://scim.aws.com/test",
                "Id": "admin-external-id",
            },
        ],
        "Name": {
            "FamilyName": "Admin",
            "GivenName": "Test",
        },
        "DisplayName": "Test Admin",
        "Emails": [
            {
                "Value": "admin@example.com",
                "Type": "work",
                "Primary": True,
            },
        ],
        "IdentityStoreId": "d-1234567890",
    },
    {
        "UserName": "alice@example.com",
        "UserId": "alice-user-id-2",
        "ExternalIds": [
            {
                "Issuer": "https://scim.aws.com/test",
                "Id": "alice-external-id",
            },
        ],
        "Name": {
            "FamilyName": "Alice",
            "GivenName": "Test",
        },
        "DisplayName": "Test Alice",
        "Emails": [
            {
                "Value": "alice@example.com",
                "Type": "work",
                "Primary": True,
            },
        ],
        "IdentityStoreId": "d-1234567890",
    },
]

# =============================================================================
# GITHUB ACTIONS WEB IDENTITY TEST MOCK DATA
# =============================================================================

# Mock CloudTrail AssumeRoleWithWebIdentity events for GitHub Actions
GITHUB_WEB_IDENTITY_CLOUDTRAIL_EVENTS = [
    {
        "EventName": "AssumeRoleWithWebIdentity",
        "EventTime": "2024-01-15T13:10:25.123000",
        "UserIdentity": {
            "type": "WebIdentityUser",
            "principalId": "repo:sublimagesec/sublimage:ref:refs/heads/main",
            "identityProvider": "token.actions.githubusercontent.com",
            "userName": "sublimagesec/sublimage",
        },
        "Resources": [
            {
                "ResourceType": "AWS::IAM::Role",
                "ResourceName": "arn:aws:iam::123456789012:role/GitHubActionsRole",
                "AccountId": "123456789012",
            }
        ],
        "CloudTrailEvent": '{"userIdentity": {"type": "WebIdentityUser", "principalId": "repo:sublimagesec/sublimage:ref:refs/heads/main", "identityProvider": "token.actions.githubusercontent.com", "userName": "sublimagesec/sublimage"}, "requestParameters": {"roleArn": "arn:aws:iam::123456789012:role/GitHubActionsRole"}, "responseElements": {"assumedRoleUser": {"arn": "arn:aws:sts::123456789012:assumed-role/GitHubActionsRole/sublimage"}}}',
    },
    {
        "EventName": "AssumeRoleWithWebIdentity",
        "EventTime": "2024-01-15T14:30:45.789000",
        "UserIdentity": {
            "type": "WebIdentityUser",
            "principalId": "repo:myorg/demo-app:ref:refs/heads/develop",
            "identityProvider": "token.actions.githubusercontent.com",
            "userName": "myorg/demo-app",
        },
        "Resources": [
            {
                "ResourceType": "AWS::IAM::Role",
                "ResourceName": "arn:aws:iam::987654321098:role/CrossAccountGitHubRole",
                "AccountId": "987654321098",
            }
        ],
        "CloudTrailEvent": '{"userIdentity": {"type": "WebIdentityUser", "principalId": "repo:myorg/demo-app:ref:refs/heads/develop", "identityProvider": "token.actions.githubusercontent.com", "userName": "myorg/demo-app"}, "requestParameters": {"roleArn": "arn:aws:iam::987654321098:role/CrossAccountGitHubRole"}, "responseElements": {"assumedRoleUser": {"arn": "arn:aws:sts::987654321098:assumed-role/CrossAccountGitHubRole/demo-app"}}}',
    },
]

# Mock AWS roles for GitHub Actions tests
GITHUB_ACTIONS_IAM_ROLES = [
    {
        "RoleName": "GitHubActionsRole",
        "RoleId": "AROA00000000000000003",
        "Arn": "arn:aws:iam::123456789012:role/GitHubActionsRole",
        "Path": "/",
        "CreateDate": "2024-01-01T10:00:00Z",
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
                    },
                    "Action": "sts:AssumeRoleWithWebIdentity",
                }
            ],
        },
    },
    {
        "RoleName": "CrossAccountGitHubRole",
        "RoleId": "AROA00000000000000004",
        "Arn": "arn:aws:iam::987654321098:role/CrossAccountGitHubRole",
        "Path": "/",
        "CreateDate": "2024-01-01T10:00:00Z",
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": "arn:aws:iam::987654321098:oidc-provider/token.actions.githubusercontent.com"
                    },
                    "Action": "sts:AssumeRoleWithWebIdentity",
                }
            ],
        },
    },
]

# GitHub Actions aggregation test data
GITHUB_ACTIONS_AGGREGATION_CLOUDTRAIL_EVENTS = [
    {
        "EventName": "AssumeRoleWithWebIdentity",
        "EventTime": "2024-01-15T09:10:25.123000",
        "UserIdentity": {
            "type": "WebIdentityUser",
            "principalId": "repo:myorg/test-repo:ref:refs/heads/main",
            "identityProvider": "token.actions.githubusercontent.com",
            "userName": "myorg/test-repo",
        },
        "Resources": [
            {
                "ResourceType": "AWS::IAM::Role",
                "ResourceName": "arn:aws:iam::111111111111:role/GitHubTestRole",
                "AccountId": "111111111111",
            }
        ],
        "CloudTrailEvent": '{"userIdentity": {"type": "WebIdentityUser", "principalId": "repo:myorg/test-repo:ref:refs/heads/main", "identityProvider": "token.actions.githubusercontent.com", "userName": "myorg/test-repo"}, "requestParameters": {"roleArn": "arn:aws:iam::111111111111:role/GitHubTestRole"}, "responseElements": {"assumedRoleUser": {"arn": "arn:aws:sts::111111111111:assumed-role/GitHubTestRole/test-repo"}}}',
    },
    {
        "EventName": "AssumeRoleWithWebIdentity",
        "EventTime": "2024-01-15T11:30:45.789000",
        "UserIdentity": {
            "type": "WebIdentityUser",
            "principalId": "repo:myorg/test-repo:ref:refs/heads/develop",
            "identityProvider": "token.actions.githubusercontent.com",
            "userName": "myorg/test-repo",
        },
        "Resources": [
            {
                "ResourceType": "AWS::IAM::Role",
                "ResourceName": "arn:aws:iam::111111111111:role/GitHubTestRole",
                "AccountId": "111111111111",
            }
        ],
        "CloudTrailEvent": '{"userIdentity": {"type": "WebIdentityUser", "principalId": "repo:myorg/test-repo:ref:refs/heads/develop", "identityProvider": "token.actions.githubusercontent.com", "userName": "myorg/test-repo"}, "requestParameters": {"roleArn": "arn:aws:iam::111111111111:role/GitHubTestRole"}, "responseElements": {"assumedRoleUser": {"arn": "arn:aws:sts::111111111111:assumed-role/GitHubTestRole/test-repo"}}}',
    },
    {
        "EventName": "AssumeRoleWithWebIdentity",
        "EventTime": "2024-01-15T14:15:30.456000",
        "UserIdentity": {
            "type": "WebIdentityUser",
            "principalId": "repo:myorg/test-repo:ref:refs/heads/main",
            "identityProvider": "token.actions.githubusercontent.com",
            "userName": "myorg/test-repo",
        },
        "Resources": [
            {
                "ResourceType": "AWS::IAM::Role",
                "ResourceName": "arn:aws:iam::111111111111:role/GitHubTestRole",
                "AccountId": "111111111111",
            }
        ],
        "CloudTrailEvent": '{"userIdentity": {"type": "WebIdentityUser", "principalId": "repo:myorg/test-repo:ref:refs/heads/main", "identityProvider": "token.actions.githubusercontent.com", "userName": "myorg/test-repo"}, "requestParameters": {"roleArn": "arn:aws:iam::111111111111:role/GitHubTestRole"}, "responseElements": {"assumedRoleUser": {"arn": "arn:aws:sts::111111111111:assumed-role/GitHubTestRole/test-repo"}}}',
    },
]

# GitHub Actions aggregation test IAM roles
GITHUB_ACTIONS_AGGREGATION_IAM_ROLES = [
    {
        "RoleName": "GitHubTestRole",
        "RoleId": "AROA00000000000000005",
        "Arn": "arn:aws:iam::111111111111:role/GitHubTestRole",
        "Path": "/",
        "CreateDate": "2024-01-01T10:00:00Z",
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": "arn:aws:iam::111111111111:oidc-provider/token.actions.githubusercontent.com"
                    },
                    "Action": "sts:AssumeRoleWithWebIdentity",
                }
            ],
        },
    },
]

# =============================================================================
# BASIC ASSUMEROLE TEST MOCK DATA
# =============================================================================

# Mock CloudTrail AssumeRole event for basic relationship test
BASIC_ASSUME_ROLE_CLOUDTRAIL_EVENTS = [
    {
        "EventName": "AssumeRole",
        "EventTime": "2024-01-15T10:30:15.123000",
        "UserIdentity": {"arn": "arn:aws:iam::123456789012:user/john.doe"},
        "Resources": [
            {
                "ResourceType": "AWS::IAM::Role",
                "ResourceName": "arn:aws:iam::123456789012:role/ApplicationRole",
                "AccountId": "123456789012",
            }
        ],
        "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::123456789012:user/john.doe"}, "requestParameters": {"roleArn": "arn:aws:iam::123456789012:role/ApplicationRole"}}',
    },
]

# =============================================================================
# AGGREGATION TEST MOCK DATA
# =============================================================================

# Mock CloudTrail AssumeRole events for aggregation test (same user/role multiple times)
AGGREGATION_ASSUME_ROLE_CLOUDTRAIL_EVENTS = [
    {
        "EventName": "AssumeRole",
        "EventTime": "2024-01-15T09:00:00.000000",
        "UserIdentity": {"arn": "arn:aws:iam::111111111111:user/test-user"},
        "Resources": [
            {
                "ResourceType": "AWS::IAM::Role",
                "ResourceName": "arn:aws:iam::111111111111:role/TestRole",
                "AccountId": "111111111111",
            }
        ],
        "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::111111111111:user/test-user"}, "requestParameters": {"roleArn": "arn:aws:iam::111111111111:role/TestRole"}}',
    },
    {
        "EventName": "AssumeRole",
        "EventTime": "2024-01-15T13:00:00.000000",
        "UserIdentity": {"arn": "arn:aws:iam::111111111111:user/test-user"},
        "Resources": [
            {
                "ResourceType": "AWS::IAM::Role",
                "ResourceName": "arn:aws:iam::111111111111:role/TestRole",
                "AccountId": "111111111111",
            }
        ],
        "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::111111111111:user/test-user"}, "requestParameters": {"roleArn": "arn:aws:iam::111111111111:role/TestRole"}}',
    },
    {
        "EventName": "AssumeRole",
        "EventTime": "2024-01-15T17:00:00.000000",
        "UserIdentity": {"arn": "arn:aws:iam::111111111111:user/test-user"},
        "Resources": [
            {
                "ResourceType": "AWS::IAM::Role",
                "ResourceName": "arn:aws:iam::111111111111:role/TestRole",
                "AccountId": "111111111111",
            }
        ],
        "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::111111111111:user/test-user"}, "requestParameters": {"roleArn": "arn:aws:iam::111111111111:role/TestRole"}}',
    },
]

# =============================================================================
# CROSS-ACCOUNT TEST MOCK DATA
# =============================================================================

# Mock CloudTrail AssumeRole event for cross-account relationship test
CROSS_ACCOUNT_ASSUME_ROLE_CLOUDTRAIL_EVENTS = [
    {
        "EventName": "AssumeRole",
        "EventTime": "2024-01-15T10:30:15.123000",
        "UserIdentity": {"arn": "arn:aws:iam::222222222222:user/cross-user"},
        "Resources": [
            {
                "ResourceType": "AWS::IAM::Role",
                "ResourceName": "arn:aws:iam::333333333333:role/ExternalRole",
                "AccountId": "333333333333",
            }
        ],
        "CloudTrailEvent": '{"userIdentity": {"arn": "arn:aws:iam::222222222222:user/cross-user"}, "requestParameters": {"roleArn": "arn:aws:iam::333333333333:role/ExternalRole"}}',
    },
]

# =============================================================================
# SAML TEST MOCK DATA
# =============================================================================

# Mock CloudTrail AssumeRoleWithSAML events for SAML relationship test
SAML_ASSUME_ROLE_CLOUDTRAIL_EVENTS = [
    {
        "EventName": "AssumeRoleWithSAML",
        "EventTime": "2024-01-15T11:45:22.456000",
        "UserIdentity": {
            "type": "SAMLUser",
            "principalId": "SAML:admin@example.com",
            "arn": "arn:aws:sts::123456789012:assumed-role/SAMLRole/admin@example.com",
            "accountId": "123456789012",
        },
        "Resources": [
            {
                "ResourceType": "AWS::IAM::Role",
                "ResourceName": "arn:aws:iam::123456789012:role/ApplicationRole",
                "AccountId": "123456789012",
            }
        ],
        "CloudTrailEvent": '{"userIdentity": {"type": "SAMLUser", "principalId": "SAML:admin@example.com", "userName": "admin@example.com"}, "requestParameters": {"roleArn": "arn:aws:iam::123456789012:role/ApplicationRole", "principalArn": "arn:aws:iam::123456789012:saml-provider/ExampleProvider"}, "responseElements": {"assumedRoleUser": {"arn": "arn:aws:sts::123456789012:assumed-role/SAMLRole/admin@example.com"}}}',
    },
    {
        "EventName": "AssumeRoleWithSAML",
        "EventTime": "2024-01-15T12:20:30.789000",
        "UserIdentity": {
            "type": "SAMLUser",
            "principalId": "SAML:alice@example.com",
            "arn": "arn:aws:sts::123456789012:assumed-role/SAMLRole/alice@example.com",
            "accountId": "123456789012",
        },
        "Resources": [
            {
                "ResourceType": "AWS::IAM::Role",
                "ResourceName": "arn:aws:iam::987654321098:role/CrossAccountRole",
                "AccountId": "987654321098",
            }
        ],
        "CloudTrailEvent": '{"userIdentity": {"type": "SAMLUser", "principalId": "SAML:alice@example.com", "userName": "alice@example.com"}, "requestParameters": {"roleArn": "arn:aws:iam::987654321098:role/CrossAccountRole", "principalArn": "arn:aws:iam::123456789012:saml-provider/ExampleProvider"}, "responseElements": {"assumedRoleUser": {"arn": "arn:aws:sts::123456789012:assumed-role/SAMLRole/alice@example.com"}}}',
    },
]
