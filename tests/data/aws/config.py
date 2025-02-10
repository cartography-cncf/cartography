LIST_CONFIGURATION_RECORDERS = [
    {
        "roleARN": "arn:aws:iam::000000000000:role/aws-service-role/config.amazonaws.com/AWSServiceRoleForConfig",
        "name": "default",
        "recordingGroup": {
            "allSupported": True,
            "includeGlobalResourceTypes": True,
        },
    },
]

LIST_DELIVERY_CHANNELS = [
    {
        "name": "default",
        "s3BucketName": "test-bucket",
    },
]

LIST_CONFIG_RULES = [
    {
        "ConfigRuleArn": "arn:aws:config:us-east-1:000000000000:config-rule/aws-service-rule/securityhub.amazonaws.com/config-rule-magmce",  # noqa:E501
        "ConfigRuleName": "securityhub-alb-http-drop-invalid-header-enabled-9d3e1985",
        "Description": "Test description",
        "Source": {
            "Owner": "AWS",
            "SourceIdentifier": "ALB_HTTP_DROP_INVALID_HEADER_ENABLED",
            "SourceDetails": [
                {
                    "EventSource": "aws.config",
                    "MessageType": "ConfigurationItemChangeNotification",
                },
            ],
        },
        "CreatedBy": "securityhub.amazonaws.com",
    },
]
