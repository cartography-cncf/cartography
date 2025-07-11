import json
from typing import Any

MOCK_EVENT_RULES_RESPONSE: dict[str, Any] = {
    "Rules": [
        {
            "Name": "hourly-batch-job",
            "Arn": "arn:aws:events:us-east-1:123456789012:rule/hourly-batch-job",
            "EventPattern": None,
            "State": "ENABLED",
            "Description": "Triggers batch job every hour",
            "ScheduleExpression": "rate(1 hour)",
            "EventBusName": "default",
            "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeRole",
        },
        {
            "Name": "ec2-state-change",
            "Arn": "arn:aws:events:us-east-1:123456789012:rule/ec2-state-change",
            "EventPattern": json.dumps(
                {
                    "source": ["aws.ec2"],
                    "detail-type": ["EC2 Instance State-change Notification"],
                }
            ),
            "State": "ENABLED",
            "Description": "React to EC2 state changes",
            "ScheduleExpression": None,
            "EventBusName": "default",
            "RoleArn": None,
        },
        {
            "Name": "cross-account-events",
            "Arn": "arn:aws:events:us-east-1:123456789012:rule/cross-account-events",
            "EventPattern": json.dumps(
                {"account": ["987654321098"], "source": ["custom.app"]}
            ),
            "State": "DISABLED",
            "Description": "Process events from partner account",
            "ScheduleExpression": None,
            "EventBusName": "custom-event-bus",
            "RoleArn": "arn:aws:iam::123456789012:role/CrossAccountRole",
            "ManagedBy": "partner-service",
        },
        {
            "Name": "codebuild-trigger",
            "Arn": "arn:aws:events:us-east-1:123456789012:rule/codebuild-trigger",
            "EventPattern": json.dumps(
                {
                    "source": ["aws.codecommit"],
                    "detail-type": ["CodeCommit Repository State Change"],
                }
            ),
            "State": "ENABLED",
            "Description": "Trigger builds on code changes",
            "ScheduleExpression": None,
            "EventBusName": "default",
            "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeRole",
        },
        {
            "Name": "pipeline-trigger",
            "Arn": "arn:aws:events:us-east-1:123456789012:rule/pipeline-trigger",
            "EventPattern": None,
            "State": "ENABLED",
            "Description": "Daily pipeline execution",
            "ScheduleExpression": "cron(0 8 * * ? *)",
            "EventBusName": "default",
            "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeRole",
        },
        {
            "Name": "api-gateway-trigger",
            "Arn": "arn:aws:events:us-east-1:123456789012:rule/api-gateway-trigger",
            "EventPattern": json.dumps(
                {"source": ["custom.myapp"], "detail-type": ["User Action"]}
            ),
            "State": "ENABLED",
            "Description": "Forward custom events to API Gateway",
            "ScheduleExpression": None,
            "EventBusName": "custom-bus",
            "RoleArn": None,
        },
        {
            "Name": "unknown-target-test",
            "Arn": "arn:aws:events:us-east-1:123456789012:rule/unknown-target-test",
            "EventPattern": json.dumps(
                {"source": ["test.service"], "detail-type": ["Test Event"]}
            ),
            "State": "ENABLED",
            "Description": "Test rule with unknown target types",
            "ScheduleExpression": None,
            "EventBusName": "default",
            "RoleArn": None,
        },
    ],
    "Targets": {
        "hourly-batch-job": [
            {
                "Id": "1",
                "Arn": "arn:aws:lambda:us-east-1:123456789012:function:ProcessBatchJob",
            },
            {
                "Id": "2",
                "Arn": "arn:aws:sns:us-east-1:123456789012:batch-notifications",
            },
        ],
        "ec2-state-change": [
            {
                "Id": "1",
                "Arn": "arn:aws:lambda:us-east-1:123456789012:function:HandleEC2StateChange",
            },
            {
                "Id": "2",
                "Arn": "arn:aws:sqs:us-east-1:123456789012:ec2-events-queue",
            },
            {
                "Id": "3",
                "Arn": "arn:aws:kinesis:us-east-1:123456789012:stream/event-stream",
            },
        ],
        "cross-account-events": [
            {
                "Id": "1",
                "Arn": "arn:aws:states:us-east-1:123456789012:stateMachine:ProcessCrossAccountEvents",
                "RoleArn": "arn:aws:iam::123456789012:role/StepFunctionRole",
            },
            {
                "Id": "2",
                "Arn": "arn:aws:ecs:us-east-1:123456789012:cluster/processing-cluster",
                "RoleArn": "arn:aws:iam::123456789012:role/ECSTaskRole",
            },
        ],
        "codebuild-trigger": [
            {
                "Id": "1",
                "Arn": "arn:aws:codebuild:us-east-1:123456789012:project/MyBuildProject",
                "RoleArn": "arn:aws:iam::123456789012:role/CodeBuildRole",
            }
        ],
        "pipeline-trigger": [
            {
                "Id": "1",
                "Arn": "arn:aws:codepipeline:us-east-1:123456789012:my-pipeline",
                "RoleArn": "arn:aws:iam::123456789012:role/CodePipelineRole",
            }
        ],
        "api-gateway-trigger": [
            {
                "Id": "1",
                "Arn": "arn:aws:execute-api:us-east-1:123456789012:abcdef123/prod/POST/webhook",
            }
        ],
        "unknown-target-test": [
            {
                "Id": "1",
                "Arn": "arn:aws:some-future-service:us-east-1:123456789012:resource/unknown-type",
            },
            {
                "Id": "2",
                "Arn": "arn:aws:custom-service:us-east-1:123456789012:widget/my-widget",
            },
        ],
    },
}
