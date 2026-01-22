from datetime import datetime

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
        "filterName": "HighErrorRate",
        "logGroupName": "/aws/lambda/process-orders",
        "filterPattern": "[errorCode = 500]",
        "metricTransformations": [
            {
                "metricName": "ErrorCount",
                "metricNamespace": "MyApp/Errors",
                "metricValue": "1",
            }
        ],
    },
    {
        "filterName": "AuthFailures",
        "logGroupName": "/aws/codebuild/sample-project",
        "filterPattern": "[statusCode = 401]",
        "metricTransformations": [
            {
                "metricName": "UnauthorizedAccess",
                "metricNamespace": "MyApp/Security",
                "metricValue": "1",
            }
        ],
    },
]

GET_CLOUDWATCH_METRIC_ALARMS = [
    {
        "AlarmName": "HighErrorCountAlarm",
        "AlarmArn": "arn:aws:cloudwatch:us-east-1:123456789012:alarm:HighErrorCountAlarm",
        "AlarmDescription": "Triggered when error count exceeds 5",
        "AlarmConfigurationUpdatedTimestamp": datetime(2023, 12, 1),
        "ActionsEnabled": True,
        "OKActions": ["arn:aws:sns:us-east-1:123456789012:ok-topic"],
        "AlarmActions": ["arn:aws:sns:us-east-1:123456789012:alarm-topic"],
        "InsufficientDataActions": [],
        "StateValue": "OK",
        "StateReason": "Threshold not breached",
        "StateReasonData": "{}",
        "StateUpdatedTimestamp": datetime(2023, 12, 1),
        "MetricName": "ErrorCount",
        "Namespace": "MyApp/Metrics",
        "Statistic": "Sum",
        "ExtendedStatistic": "",
        "Dimensions": [{"Name": "LogGroupName", "Value": "/aws/lambda/serviceA"}],
        "Period": 300,
        "Unit": "Count",
        "EvaluationPeriods": 1,
        "DatapointsToAlarm": 1,
        "Threshold": 5.0,
        "ComparisonOperator": "GreaterThanThreshold",
        "TreatMissingData": "missing",
        "EvaluateLowSampleCountPercentile": "",
        "Metrics": [],
        "ThresholdMetricId": "",
        "EvaluationState": "PARTIAL_DATA",
        "StateTransitionedTimestamp": datetime(2023, 12, 1),
    },
    {
        "AlarmName": "CompositeErrorRateAlarm",
        "AlarmArn": "arn:aws:cloudwatch:us-east-1:123456789012:alarm:CompositeErrorRateAlarm",
        "AlarmDescription": "Alarm on combined ErrorCount and WarningCount",
        "AlarmConfigurationUpdatedTimestamp": datetime(2023, 12, 2),
        "ActionsEnabled": True,
        "OKActions": [],
        "AlarmActions": ["arn:aws:sns:us-east-1:123456789012:composite-topic"],
        "InsufficientDataActions": [],
        "StateValue": "INSUFFICIENT_DATA",
        "StateReason": "Waiting for datapoints",
        "StateReasonData": "{}",
        "StateUpdatedTimestamp": datetime(2023, 12, 2),
        "MetricName": "",
        "Namespace": "",
        "Statistic": "",
        "ExtendedStatistic": "",
        "Dimensions": [],
        "Period": 0,
        "Unit": "None",
        "EvaluationPeriods": 2,
        "DatapointsToAlarm": 2,
        "Threshold": 10.0,
        "ComparisonOperator": "GreaterThanThreshold",
        "TreatMissingData": "notBreaching",
        "EvaluateLowSampleCountPercentile": "",
        "Metrics": [
            {
                "Id": "m1",
                "MetricStat": {
                    "Metric": {
                        "Namespace": "MyApp/Metrics",
                        "MetricName": "ErrorCount",
                        "Dimensions": [
                            {"Name": "LogGroupName", "Value": "/aws/lambda/serviceA"}
                        ],
                    },
                    "Period": 300,
                    "Stat": "Sum",
                    "Unit": "Count",
                },
                "ReturnData": False,
                "AccountId": "123456789012",
            },
            {
                "Id": "m2",
                "MetricStat": {
                    "Metric": {
                        "Namespace": "MyApp/Metrics",
                        "MetricName": "WarningCount",
                        "Dimensions": [
                            {"Name": "LogGroupName", "Value": "/aws/lambda/serviceA"}
                        ],
                    },
                    "Period": 300,
                    "Stat": "Sum",
                    "Unit": "Count",
                },
                "ReturnData": False,
                "AccountId": "123456789012",
            },
            {
                "Id": "e1",
                "Expression": "m1 + m2",
                "Label": "TotalIssues",
                "ReturnData": True,
            },
        ],
        "ThresholdMetricId": "e1",
        "EvaluationState": "PARTIAL_DATA",
        "StateTransitionedTimestamp": datetime(2023, 12, 2),
    },
]
