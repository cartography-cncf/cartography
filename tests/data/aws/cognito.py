GET_POOLS = [
    {
        "IdentityPoolId": "us-east-1:abcd1234-5678-90ef-ghij-klmnopqrstuv",
        "IdentityPoolName": "CartographyTestPool",
    },
]


GET_COGNITO_IDENTITY_POOLS = [
    {
        "IdentityPoolId": "us-east-1:abcd1234-5678-90ef-ghij-klmnopqrstuv",
        "Roles": {
            "authenticated": "arn:aws:iam::1234:role/cartography-read-only",
            "unauthenticated": "arn:aws:iam::1234:role/cartography-service",
        },
        "RoleMappings": {
            "cognito-idp.us-east-1.amazonaws.com/us-east-1_ExamplePool": {
                "Type": "Rules",
                "AmbiguousRoleResolution": "AuthenticatedRole",
                "RulesConfiguration": {
                    "Rules": [
                        {
                            "Claim": "custom:role",
                            "MatchType": "Equals",
                            "Value": "admin",
                            "RoleARN": "arn:aws:iam::111122223333:role/AdminRole",
                        },
                        {
                            "Claim": "custom:role",
                            "MatchType": "Equals",
                            "Value": "user",
                            "RoleARN": "arn:aws:iam::111122223333:role/UserRole",
                        },
                    ]
                },
            }
        },
    }
]
