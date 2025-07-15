GET_CLOUDWATCH_LOG_GROUPS = [
    {
        "logGroupName": "/aws/lambda/process-orders",
        "creationTime": 1685548800000,
        "retentionInDays": 14,
        "metricFilterCount": 2,
        "storedBytes": 10485760,
        "kmsKeyId": "arn:aws:kms:eu-west-1:123456789012:key/abcde123-4567-890a-bcde-1234567890ab",
        "dataProtectionStatus": "ACTIVATED",
        "inheritedProperties": ["ACCOUNT_DATA_PROTECTION"],
        "logGroupClass": "STANDARD",
        "logGroupArn": "arn:aws:logs:eu-west-1:123456789012:log-group:/aws/lambda/process-orders",
    },
    {
        "logGroupName": "/aws/codebuild/sample-project",
        "creationTime": 1687648800000,
        "retentionInDays": 30,
        "metricFilterCount": 1,
        "storedBytes": 20485760,
        "kmsKeyId": "",
        "dataProtectionStatus": "DISABLED",
        "inheritedProperties": [],
        "logGroupClass": "INFREQUENT_ACCESS",
        "logGroupArn": "arn:aws:logs:eu-west-1:123456789012:log-group:/aws/codebuild/sample-project",
    },
]

GET_CLOUDWATCH_LOG_METRIC_FILTERS = [
    {
        "filterName": "LambdaErrorCount",
        "logGroupName": "/aws/lambda/process-orders",
        "filterPattern": "[timestamp=*Z, request_id=\"*-*\", event]",
        "metricTransformations": [
            {
                "metricName": "ErrorCount",
                "metricNamespace": "MyApp/Metrics",
                "metricValue": "1",
                "defaultValue": 0.0
            }
        ],
        "creationTime": 1685549800000,
    },
    {
        "filterName": "BuildDuration",
        "logGroupName": "/aws/codebuild/sample-project",
        "filterPattern": "[duration=*]",
        "metricTransformations": [
            {
                "metricName": "BuildDuration",
                "metricNamespace": "CodeBuild/Metrics",
                "metricValue": "$duration",
                "defaultValue": 0.0
            }
        ],
        "creationTime": 1687650000000,
    },
]
