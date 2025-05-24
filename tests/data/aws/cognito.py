import datetime

DESCRIBE_COGNITO_USER_POOL = {
    [
        {
            "UserPool": {
                "Id": "us-east-1_iShbQMpc7",
                "Name": "User pool - th7n0",
                "Policies": {
                    "PasswordPolicy": {
                        "MinimumLength": 8,
                        "RequireUppercase": True,
                        "RequireLowercase": True,
                        "RequireNumbers": True,
                        "RequireSymbols": True,
                        "TemporaryPasswordValidityDays": 7,
                    },
                    "SignInPolicy": {"AllowedFirstAuthFactors": ["PASSWORD"]},
                },
                "DeletionProtection": "ACTIVE",
                "LambdaConfig": {},
                "LastModifiedDate": datetime.datetime(2025, 5, 19, 10, 1, 16, 981000),
                "CreationDate": datetime.datetime(2025, 5, 19, 10, 1, 16, 981000),
                "SchemaAttributes": [
                    {
                        "Name": "profile",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": False,
                        "StringAttributeConstraints": {
                            "MinLength": "0",
                            "MaxLength": "2048",
                        },
                    },
                    {
                        "Name": "address",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": False,
                        "StringAttributeConstraints": {
                            "MinLength": "0",
                            "MaxLength": "2048",
                        },
                    },
                    {
                        "Name": "birthdate",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": True,
                        "StringAttributeConstraints": {
                            "MinLength": "10",
                            "MaxLength": "10",
                        },
                    },
                    {
                        "Name": "gender",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": False,
                        "StringAttributeConstraints": {
                            "MinLength": "0",
                            "MaxLength": "2048",
                        },
                    },
                    {
                        "Name": "preferred_username",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": False,
                        "StringAttributeConstraints": {
                            "MinLength": "0",
                            "MaxLength": "2048",
                        },
                    },
                    {
                        "Name": "updated_at",
                        "AttributeDataType": "Number",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": False,
                        "NumberAttributeConstraints": {"MinValue": "0"},
                    },
                    {
                        "Name": "website",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": False,
                        "StringAttributeConstraints": {
                            "MinLength": "0",
                            "MaxLength": "2048",
                        },
                    },
                    {
                        "Name": "picture",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": False,
                        "StringAttributeConstraints": {
                            "MinLength": "0",
                            "MaxLength": "2048",
                        },
                    },
                    {
                        "Name": "identities",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": False,
                        "StringAttributeConstraints": {},
                    },
                    {
                        "Name": "sub",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": False,
                        "Required": True,
                        "StringAttributeConstraints": {
                            "MinLength": "1",
                            "MaxLength": "2048",
                        },
                    },
                    {
                        "Name": "phone_number",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": False,
                        "StringAttributeConstraints": {
                            "MinLength": "0",
                            "MaxLength": "2048",
                        },
                    },
                    {
                        "Name": "phone_number_verified",
                        "AttributeDataType": "Boolean",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": False,
                    },
                    {
                        "Name": "zoneinfo",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": False,
                        "StringAttributeConstraints": {
                            "MinLength": "0",
                            "MaxLength": "2048",
                        },
                    },
                    {
                        "Name": "locale",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": False,
                        "StringAttributeConstraints": {
                            "MinLength": "0",
                            "MaxLength": "2048",
                        },
                    },
                    {
                        "Name": "email",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": True,
                        "StringAttributeConstraints": {
                            "MinLength": "0",
                            "MaxLength": "2048",
                        },
                    },
                    {
                        "Name": "email_verified",
                        "AttributeDataType": "Boolean",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": False,
                    },
                    {
                        "Name": "given_name",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": False,
                        "StringAttributeConstraints": {
                            "MinLength": "0",
                            "MaxLength": "2048",
                        },
                    },
                    {
                        "Name": "family_name",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": True,
                        "StringAttributeConstraints": {
                            "MinLength": "0",
                            "MaxLength": "2048",
                        },
                    },
                    {
                        "Name": "middle_name",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": False,
                        "StringAttributeConstraints": {
                            "MinLength": "0",
                            "MaxLength": "2048",
                        },
                    },
                    {
                        "Name": "name",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": True,
                        "StringAttributeConstraints": {
                            "MinLength": "0",
                            "MaxLength": "2048",
                        },
                    },
                    {
                        "Name": "nickname",
                        "AttributeDataType": "String",
                        "DeveloperOnlyAttribute": False,
                        "Mutable": True,
                        "Required": False,
                        "StringAttributeConstraints": {
                            "MinLength": "0",
                            "MaxLength": "2048",
                        },
                    },
                ],
                "AutoVerifiedAttributes": ["email"],
                "AliasAttributes": ["email"],
                "VerificationMessageTemplate": {
                    "DefaultEmailOption": "CONFIRM_WITH_CODE"
                },
                "UserAttributeUpdateSettings": {
                    "AttributesRequireVerificationBeforeUpdate": []
                },
                "MfaConfiguration": "OFF",
                "EstimatedNumberOfUsers": 2,
                "EmailConfiguration": {"EmailSendingAccount": "COGNITO_DEFAULT"},
                "UserPoolTags": {},
                "Domain": "us-east-1ishbqmpc7",
                "AdminCreateUserConfig": {
                    "AllowAdminCreateUserOnly": False,
                    "UnusedAccountValidityDays": 7,
                },
                "UsernameConfiguration": {"CaseSensitive": False},
                "Arn": "arn:aws:cognito-idp:us-east-1:593793048302:userpool/us-east-1_iShbQMpc7",
                "AccountRecoverySetting": {
                    "RecoveryMechanisms": [
                        {"Priority": 1, "Name": "verified_email"},
                        {"Priority": 2, "Name": "verified_phone_number"},
                    ]
                },
                "UserPoolTier": "ESSENTIALS",
            },
            "ResponseMetadata": {
                "RequestId": "016071b3-20d3-4f32-9bb5-ae81940b1ee0",
                "HTTPStatusCode": 200,
                "HTTPHeaders": {
                    "date": "Fri, 23 May 2025 00:55:43 GMT",
                    "content-type": "application/x-amz-json-1.1",
                    "content-length": "4770",
                    "connection": "keep-alive",
                    "x-amzn-requestid": "016071b3-20d3-4f32-9bb5-ae81940b1ee0",
                },
                "RetryAttempts": 0,
            },
        }
    ]
}
