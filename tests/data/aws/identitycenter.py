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
