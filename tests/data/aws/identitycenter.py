LIST_USERS = [
    {
        "UserName": "test.user1@example.com",
        "UserId": "aaaaaaaa-a0d1-aaac-5af0-59c813ec7671",
        "ExternalIds": [
            {
                "Issuer": "https://scim.aws.com/1223122",
                "Id": "00aaaaabbbbb",
            },
        ],
        "Name": {
            "FamilyName": "User",
            "GivenName": "Test",
        },
        "DisplayName": "Test User 1",
        "NickName": "TestUser1",
        "Emails": [
            {
                "Value": "test.user1@example.com",
                "Type": "work",
                "Primary": True,
            },
        ],
        "Addresses": [
            {
                "Country": "US",
                "Primary": True,
            },
        ],
        "Title": "Test User",
        "IdentityStoreId": "d-1234567890",
    },
]

LIST_GROUPS = [
    {
        "DisplayName": "Test Group",
        "GroupId": "gggggggg-a0d1-aaac-5af0-59c813ec7671",
        "ExternalIds": [
            {
                "Issuer": "https://scim.aws.com/1223122",
                "Id": "00ggggghhhhh",
            },
        ],
        "Description": "Example AWS Identity Center group.",
        "IdentityStoreId": "d-1234567890",
    },
]

LIST_INSTANCES = [
    {
        "InstanceArn": "arn:aws:sso:::instance/ssoins-12345678901234567",
        "IdentityStoreId": "d-1234567890",
        "InstanceStatus": "ACTIVE",
        "CreatedDate": "2023-01-01T00:00:00Z",
        "LastModifiedDate": "2023-01-01T00:00:00Z",
    },
]

LIST_PERMISSION_SETS = [
    {
        "Name": "AdministratorAccess",
        "PermissionSetArn": "arn:aws:sso:::permissionSet/ssoins-12345678901234567/ps-12345678901234567",
        "Description": "Provides full access to AWS services and resources.",
        "CreatedDate": "2023-01-01T00:00:00Z",
        "SessionDuration": "PT12H",
    },
]

# Mock AWS roles that correspond to permission sets
# us-east-1 role (no region in path) with realistic suffix
MOCK_AWS_ROLE_US_EAST_1 = {
    "Arn": "arn:aws:iam::123456789012:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_AdministratorAccess_y5z6a7b8c9d0e1f2",
    "RoleName": "AWSReservedSSO_AdministratorAccess_y5z6a7b8c9d0e1f2",
    "RoleId": "AIDACKCEVSQ6C2EXAMPLE",
    "CreateDate": "2023-01-01T00:00:00Z",
    "Path": "/aws-reserved/sso.amazonaws.com/",
}

# us-west-2 role (includes region in path) with realistic suffix
MOCK_AWS_ROLE_US_WEST_2 = {
    "Arn": "arn:aws:iam::123456789012:role/aws-reserved/sso.amazonaws.com/us-west-2/AWSReservedSSO_AdministratorAccess_g3h4i5j6k7l8m9n0",
    "RoleName": "AWSReservedSSO_AdministratorAccess_g3h4i5j6k7l8m9n0",
    "RoleId": "AIDACKCEVSQ6C2EXAMPLE",
    "CreateDate": "2023-01-01T00:00:00Z",
    "Path": "/aws-reserved/sso.amazonaws.com/us-west-2/",
}

# Mock data for multi-account permission set assignment test
# This tests that a user assigned to a permission set on 2 out of 3 accounts
# only gets ALLOWED_BY relationships to those 2 accounts, not all 3

MULTI_ACCOUNT_TEST_ACCOUNTS = [
    "111111111111",  # Account 1 - user HAS assignment
    "222222222222",  # Account 2 - user HAS assignment
    "333333333333",  # Account 3 - user does NOT have assignment
]

# Mock IAM roles for the AdministratorAccess permission set in each account
# Role names must match the format: AWSReservedSSO_{PermissionSetName}_{random_suffix}
# The suffix is a random hash appended by AWS when provisioning the permission set
MULTI_ACCOUNT_TEST_ROLES = [
    {
        "Arn": "arn:aws:iam::111111111111:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_AdministratorAccess_a1b2c3d4e5f6g7h8",
        "RoleName": "AWSReservedSSO_AdministratorAccess_a1b2c3d4e5f6g7h8",
        "RoleId": "AIDAROLE1EXAMPLE",
        "CreateDate": "2023-01-01T00:00:00Z",
        "Path": "/aws-reserved/sso.amazonaws.com/",
        "AccountId": "111111111111",
    },
    {
        "Arn": "arn:aws:iam::222222222222:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_AdministratorAccess_i9j0k1l2m3n4o5p6",
        "RoleName": "AWSReservedSSO_AdministratorAccess_i9j0k1l2m3n4o5p6",
        "RoleId": "AIDAROLE2EXAMPLE",
        "CreateDate": "2023-01-01T00:00:00Z",
        "Path": "/aws-reserved/sso.amazonaws.com/",
        "AccountId": "222222222222",
    },
    {
        "Arn": "arn:aws:iam::333333333333:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_AdministratorAccess_q7r8s9t0u1v2w3x4",
        "RoleName": "AWSReservedSSO_AdministratorAccess_q7r8s9t0u1v2w3x4",
        "RoleId": "AIDAROLE3EXAMPLE",
        "CreateDate": "2023-01-01T00:00:00Z",
        "Path": "/aws-reserved/sso.amazonaws.com/",
        "AccountId": "333333333333",
    },
]

# User is assigned to the permission set on accounts 1 and 2 only
# Note: RoleArn is not included here - it's added by get_principal_roles() during sync
MULTI_ACCOUNT_USER_ASSIGNMENTS = [
    {
        "UserId": "aaaaaaaa-a0d1-aaac-5af0-59c813ec7671",
        "PermissionSetArn": "arn:aws:sso:::permissionSet/ssoins-12345678901234567/ps-12345678901234567",
        "AccountId": "111111111111",
    },
    {
        "UserId": "aaaaaaaa-a0d1-aaac-5af0-59c813ec7671",
        "PermissionSetArn": "arn:aws:sso:::permissionSet/ssoins-12345678901234567/ps-12345678901234567",
        "AccountId": "222222222222",
    },
    # Note: No assignment for account 333333333333
]
