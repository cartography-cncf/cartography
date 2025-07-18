DESCRIBE_CLOUDTRAIL_TRAILS = [
    {
        "Name": "test-trail",
        "HomeRegion": "us-east-1",
        "TrailARN": "arn:aws:cloudtrail:us-east-1:123456789012:trail/test-trail",
        "IsMultiRegionTrail": True,
        "IsOrganizationTrail": False,
        "LogFileValidationEnabled": True,
        "S3BucketName": "test-bucket",
        "S3KeyPrefix": "test-prefix",
        "IncludeGlobalServiceEvents": True,
        "HasCustomEventSelectors": False,
        "HasInsightSelectors": False,
        "KmsKeyId": "arn:aws:kms:us-east-1:123456789012:key/test-key",
        "CloudWatchLogsLogGroupArn": "arn:aws:logs:eu-west-1:123456789012:log-group:/aws/lambda/process-orders:*",
    }
]

BUCKETS = {
    "Buckets": [
        {
            "Name": "test-bucket",
            "Region": "us-east-1",
            "CreationDate": "2021-01-01",
        }
    ]
}
