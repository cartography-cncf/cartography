from cartography.intel.aws.eventbridge import classify_target_arn
from cartography.intel.aws.eventbridge import transform
from tests.data.aws.eventbridge.event_rules import MOCK_EVENT_RULES_RESPONSE


def test_transform():
    region = "us-east-1"
    rules, targets = transform(MOCK_EVENT_RULES_RESPONSE, region)

    assert len(rules) == 7
    assert len(targets) == 12

    hourly_job = next(r for r in rules if r["Name"] == "hourly-batch-job")
    assert hourly_job["ScheduleExpression"] == "rate(1 hour)"

    lambda_target = next(
        t
        for t in targets
        if t["Arn"].startswith("arn:aws:lambda") and t["RuleArn"] == hourly_job["Arn"]
    )
    assert lambda_target["Id"] == "1"


def test_transform_handles_missing_fields():
    minimal_data = {
        "Rules": [
            {"Name": "minimal", "Arn": "arn:aws:events:us-east-1:123:rule/minimal"}
        ],
        "Targets": {},
    }
    rules, targets = transform(minimal_data, "us-east-1")
    assert rules[0]["EventBusName"] == "default"
    assert targets == []


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
