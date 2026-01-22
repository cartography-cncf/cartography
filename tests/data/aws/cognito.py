from datetime import datetime

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

GET_COGNITO_USER_POOLS = [
    {
        "Id": "us-east-1_abc123",
        "Name": "TestUserPoolOne",
        "LambdaConfig": {
            "PreSignUp": "arn:aws:lambda:us-east-1:123456789012:function:PreSignUpHook",
            "CustomMessage": "arn:aws:lambda:us-east-1:123456789012:function:CustomMessageHook",
            "PostConfirmation": "arn:aws:lambda:us-east-1:123456789012:function:PostConfirmHook",
            "PreAuthentication": "arn:aws:lambda:us-east-1:123456789012:function:PreAuthHook",
            "PostAuthentication": "arn:aws:lambda:us-east-1:123456789012:function:PostAuthHook",
            "DefineAuthChallenge": "arn:aws:lambda:us-east-1:123456789012:function:DefineAuthHook",
            "CreateAuthChallenge": "arn:aws:lambda:us-east-1:123456789012:function:CreateAuthHook",
            "VerifyAuthChallengeResponse": "arn:aws:lambda:us-east-1:123456789012:function:VerifyAuthHook",
            "PreTokenGeneration": "arn:aws:lambda:us-east-1:123456789012:function:PreTokenHook",
            "UserMigration": "arn:aws:lambda:us-east-1:123456789012:function:UserMigrationHook",
            "PreTokenGenerationConfig": {
                "LambdaVersion": "V1_0",
                "LambdaArn": "arn:aws:lambda:us-east-1:123456789012:function:PreTokenConfigHook",
            },
            "CustomSMSSender": {
                "LambdaVersion": "V1_0",
                "LambdaArn": "arn:aws:lambda:us-east-1:123456789012:function:SMSSenderHook",
            },
            "CustomEmailSender": {
                "LambdaVersion": "V1_0",
                "LambdaArn": "arn:aws:lambda:us-east-1:123456789012:function:EmailSenderHook",
            },
            "KMSKeyID": "arn:aws:kms:us-east-1:123456789012:key/abcde-12345-fghij-67890",
        },
        "Status": "Enabled",
        "LastModifiedDate": datetime(2024, 1, 10),
        "CreationDate": datetime(2023, 12, 25),
    },
    {
        "Id": "us-west-2_xyz789",
        "Name": "TestUserPoolTwo",
        "LambdaConfig": {
            "PreSignUp": "arn:aws:lambda:us-west-2:987654321098:function:PreSignUpHookTwo",
            "CustomMessage": "arn:aws:lambda:us-west-2:987654321098:function:CustomMessageHookTwo",
            "PostConfirmation": "arn:aws:lambda:us-west-2:987654321098:function:PostConfirmHookTwo",
            "PreAuthentication": "arn:aws:lambda:us-west-2:987654321098:function:PreAuthHookTwo",
            "PostAuthentication": "arn:aws:lambda:us-west-2:987654321098:function:PostAuthHookTwo",
            "DefineAuthChallenge": "arn:aws:lambda:us-west-2:987654321098:function:DefineAuthHookTwo",
            "CreateAuthChallenge": "arn:aws:lambda:us-west-2:987654321098:function:CreateAuthHookTwo",
            "VerifyAuthChallengeResponse": "arn:aws:lambda:us-west-2:987654321098:function:VerifyAuthHookTwo",
            "PreTokenGeneration": "arn:aws:lambda:us-west-2:987654321098:function:PreTokenHookTwo",
            "UserMigration": "arn:aws:lambda:us-west-2:987654321098:function:UserMigrationHookTwo",
            "PreTokenGenerationConfig": {
                "LambdaVersion": "V2_0",
                "LambdaArn": "arn:aws:lambda:us-west-2:987654321098:function:PreTokenConfigHookTwo",
            },
            "CustomSMSSender": {
                "LambdaVersion": "V1_0",
                "LambdaArn": "arn:aws:lambda:us-west-2:987654321098:function:SMSSenderHookTwo",
            },
            "CustomEmailSender": {
                "LambdaVersion": "V1_0",
                "LambdaArn": "arn:aws:lambda:us-west-2:987654321098:function:EmailSenderHookTwo",
            },
            "KMSKeyID": "arn:aws:kms:us-west-2:987654321098:key/zyxwv-98765-lkjhg-43210",
        },
        "Status": "Disabled",
        "LastModifiedDate": datetime(2024, 6, 5),
        "CreationDate": datetime(2024, 1, 30),
    },
]
