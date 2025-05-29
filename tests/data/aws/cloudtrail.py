LIST_CLOUDTRAIL_TRAILS = [
    {
        "TrailARN": "arn:aws:cloudtrail:eu-west-1:000000000000:trail/test-trail",
        "Name": "test-trail",
        "HomeRegion": "eu-west-1",
    }
]

GET_CLOUDTRAIL_TRAIL = {
    "Name": "test-trail",
    "HomeRegion": "eu-west-1",
    "TrailARN": "arn:aws:cloudtrail:eu-west-1:000000000000:trail/test-trail",
    "IsMultiRegionTrail": True,
    "IsOrganizationTrail": False,
    "LogFileValidationEnabled": True,
    "S3BucketName": "test-bucket",
    "S3KeyPrefix": "test-prefix",
    "SnsTopicARN": "arn:aws:sns:eu-west-1:000000000000:test-topic",
    "IncludeGlobalServiceEvents": True,
    "IsMultiRegionTrail": True,
    "HasCustomEventSelectors": False,
    "HasInsightSelectors": False,
    "KmsKeyId": "9a1ad414-6e3b-47ce-8366-6b8f26ba467d",
    "CloudWatchLogsLogGroupArn": "arn:aws:logs:eu-west-1:000000000000:log-group:/aws/codebuild/sample-project",
}
