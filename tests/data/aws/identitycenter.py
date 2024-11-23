LIST_USERS = [
    {
        "UserName": "nobody@nobody.com",
        "UserId": "aaaaaaaa-a0d1-aaac-5af0-59c813ec7671",
        "ExternalIds": [
            {
                    "Issuer": "https://scim.aws.com/1223122",
                    "Id": "00aaaaabbbbb",
            },
        ],
        "Name": {
            "FamilyName": "Jones",
            "GivenName": "Mr.",
        },
        "DisplayName": "Mr. Jones",
        "NickName": "Jonsey",
        "Emails": [
            {
                    "Value": "mr.jones@mycompany.com",
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
        "Title": "Singer, On the Internet",
        "IdentityStoreId": "d-12345",
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
