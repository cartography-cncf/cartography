from cartography.intel.aws.eventbridge import classify_target_arn
from cartography.intel.aws.eventbridge import transform_event_rules
from tests.data.aws.eventbridge.event_rules import MOCK_EVENT_RULES_RESPONSE

def test_transform_event_rules():
    region = "us-east-1"
    result = transform_event_rules(MOCK_EVENT_RULES_RESPONSE, region)
    assert len(result) == 7

    hourly_job = next(r for r in result if r["Name"] == "hourly-batch-job")
    assert hourly_job["ScheduleExpression"] == "rate(1 hour)"
    assert hourly_job["lambda_functions_arns"] == [
        "arn:aws:lambda:us-east-1:123456789012:function:ProcessBatchJob"
    ]
    assert hourly_job["sns_topics_arns"] == [
        "arn:aws:sns:us-east-1:123456789012:batch-notifications"
    ]

    ec2_rule = next(r for r in result if r["Name"] == "ec2-state-change")
    assert ec2_rule["sqs_queues_arns"] == [
        "arn:aws:sqs:us-east-1:123456789012:ec2-events-queue"
    ]

    cross_rule = next(r for r in result if r["Name"] == "cross-account-events")
    assert cross_rule["step_functions_arns"] == [
        "arn:aws:states:us-east-1:123456789012:stateMachine:ProcessCrossAccountEvents"
    ]

def test_transform_event_rules_handles_missing_fields():
    minimal_data = {"Rules": [{"Name": "minimal", "Arn": "arn:aws:events:us-east-1:123:rule/minimal"}], "Targets": {}}
    result = transform_event_rules(minimal_data, "us-east-1")
    assert result[0]["EventBusName"] == "default"

def test_classify_target_arn():
    cases = [
        ("arn:aws:lambda:us-east-1:123:function:test", "lambda_functions"),
        ("arn:aws:sns:us-east-1:123:topic", "sns_topics"),
        ("arn:aws:sqs:us-east-1:123:queue", "sqs_queues"),
        ("arn:aws:ecs:us-east-1:123:cluster/test", "ecs_clusters"),
        ("arn:aws:states:us-east-1:123:stateMachine:test", "step_functions"),
        ("arn:aws:kinesis:us-east-1:123:stream/test", "kinesis_streams"),
        ("arn:aws:codebuild:us-east-1:123:project/test", "codebuild_projects"),
        ("arn:aws:codepipeline:us-east-1:123:test", "codepipelines"),
        ("arn:aws:execute-api:us-east-1:123:test", "api_gateways"),
        ("arn:aws:logs:us-east-1:123:log-group:test", "cloudwatch_log_groups"),
        ("invalid-arn", "unknown"),
    ]

    for arn, expected_type in cases:
        assert classify_target_arn(arn)[0] == expected_type 

