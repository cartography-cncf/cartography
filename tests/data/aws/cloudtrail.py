LIST_CLOUDTRAIL_TRAILS = [
    {
        "TrailARN": "arn:aws:cloudtrail:us-east-1:123456789012:trail/test-trail",
        "Name": "test-trail",
        "HomeRegion": "us-east-1",
    }
]

GET_CLOUDTRAIL_TRAIL = {
    "Name": "test-trail",
    "HomeRegion": "us-east-1",
    "TrailARN": "arn:aws:cloudtrail:us-east-1:123456789012:trail/test-trail",
    "IsMultiRegionTrail": True,
    "IsOrganizationTrail": False,
    "LogFileValidationEnabled": True,
    "S3BucketName": "test-bucket",
    "S3KeyPrefix": "test-prefix",
    "IncludeGlobalServiceEvents": True,
    "IsMultiRegionTrail": True,
    "HasCustomEventSelectors": False,
    "HasInsightSelectors": False,
    "KmsKeyId": "arn:aws:kms:us-east-1:123456789012:key/test-key",
    "CloudWatchLogsLogGroupArn": "arn:aws:logs:us-east-1:123456789012:log-group:test-log-group",
}
