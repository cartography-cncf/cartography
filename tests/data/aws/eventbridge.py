GET_EVENTBRIDGE_RULES = [
    {
        "Name": "UserSignupRule",
        "Arn": "arn:aws:events:us-east-1:123456789012:rule/UserSignupRule",
        "EventPattern": '{"source": ["my.app"], "detail-type": ["user.signup"]}',
        "State": "ENABLED",
        "Description": "Triggers on new user signup events",
        "ScheduleExpression": "",
        "RoleArn": "arn:aws:iam::1234:role/cartography-read-only",
        "ManagedBy": "my-service",
        "EventBusName": "default",
    },
    {
        "Name": "DailyCleanupRule",
        "Arn": "arn:aws:events:us-east-1:123456789012:rule/DailyCleanupRule",
        "EventPattern": "",
        "State": "ENABLED",
        "Description": "Runs daily cleanup job",
        "ScheduleExpression": "rate(1 day)",
        "RoleArn": "arn:aws:iam::1234:role/cartography-service",
        "ManagedBy": "scheduler-service",
        "EventBusName": "default",
    },
]

GET_EVENTBRIDGE_TARGETS = [
    {
        "Id": "Target1",
        "Arn": "arn:aws:lambda:us-east-1:123456789012:function:ProcessSignup",
        "RuleArn": "arn:aws:events:us-east-1:123456789012:rule/UserSignupRule",
        "RoleArn": "arn:aws:iam::1234:role/cartography-read-only",
        "Input": '{"userId": "$.detail.userId"}',
        "InputPath": "$.detail",
        "InputTransformer": None,
        "Region": "us-east-1",
    },
    {
        "Id": "Target2",
        "Arn": "arn:aws:sns:us-east-1:123456789012:NotifyAdmin",
        "RuleArn": "arn:aws:events:us-east-1:123456789012:rule/DailyCleanupRule",
        "RoleArn": "arn:aws:iam::1234:role/cartography-service",
        "Input": None,
        "InputPath": None,
        "InputTransformer": None,
        "Region": "us-east-1",
    },
]
