from unittest.mock import patch

import cartography.intel.aws.eventbridge
from cartography.intel.aws.eventbridge import sync
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "123456789012"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 1234567890

MOCK_EVENT_RULES_RESPONSE = {
    "Rules": [
        {
            "Name": "hourly-lambda-trigger",
            "Arn": (
                "arn:aws:events:us-east-1:123456789012:rule/" "hourly-lambda-trigger"
            ),
            "State": "ENABLED",
            "Description": "Triggers Lambda every hour",
            "ScheduleExpression": "rate(1 hour)",
            "EventBusName": "default",
            "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeRole",
        },
        {
            "Name": "ec2-state-monitor",
            "Arn": ("arn:aws:events:us-east-1:123456789012:rule/" "ec2-state-monitor"),
            "State": "ENABLED",
            "Description": "Monitor EC2 state changes",
            "EventPattern": (
                '{"source": ["aws.ec2"], "detail-type": '
                '["EC2 Instance State-change Notification"]}'
            ),
            "EventBusName": "default",
        },
    ],
    "Targets": {
        "hourly-lambda-trigger": [
            {
                "Id": "1",
                "Arn": (
                    "arn:aws:lambda:us-east-1:123456789012:function:" "ProcessHourlyJob"
                ),
            },
        ],
        "ec2-state-monitor": [
            {
                "Id": "1",
                "Arn": "arn:aws:sns:us-east-1:123456789012:ec2-alerts",
            },
            {
                "Id": "2",
                "Arn": "arn:aws:sqs:us-east-1:123456789012:ec2-state-queue",
            },
        ],
    },
}


@patch.object(
    cartography.intel.aws.eventbridge,
    "get_event_rules",
    return_value=MOCK_EVENT_RULES_RESPONSE,
)
def test_sync_event_rules(mock_get_rules, neo4j_session):
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AWS_ID": TEST_ACCOUNT_ID,
    }

    neo4j_session.run(
        """
        MERGE (a:AWSAccount {id: $account_id})
        SET a.lastupdated = $update_tag
        """,
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    neo4j_session.run(
        """
        MERGE (lambda:AWSLambda {
            id: 'arn:aws:lambda:us-east-1:123456789012:function:ProcessHourlyJob'
        })
        MERGE (sns:SNSTopic {
            arn: 'arn:aws:sns:us-east-1:123456789012:ec2-alerts'
        })
        MERGE (sqs:SQSQueue {
            arn: 'arn:aws:sqs:us-east-1:123456789012:ec2-state-queue'
        })
        MERGE (role:AWSRole {
            arn: 'arn:aws:iam::123456789012:role/EventBridgeRole'
        })
        """
    )

    sync(
        neo4j_session,
        None,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    expected_nodes = {
        (
            "arn:aws:events:us-east-1:123456789012:rule/hourly-lambda-trigger",
            "hourly-lambda-trigger",
            "ENABLED",
        ),
        (
            "arn:aws:events:us-east-1:123456789012:rule/ec2-state-monitor",
            "ec2-state-monitor",
            "ENABLED",
        ),
    }
    assert (
        check_nodes(neo4j_session, "EventRule", ["arn", "name", "state"])
        == expected_nodes
    )

    expected_account_rels = {
        (
            "arn:aws:events:us-east-1:123456789012:rule/hourly-lambda-trigger",
            TEST_ACCOUNT_ID,
        ),
        (
            "arn:aws:events:us-east-1:123456789012:rule/ec2-state-monitor",
            TEST_ACCOUNT_ID,
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "EventRule",
            "arn",
            "AWSAccount",
            "id",
            "RESOURCE",
            rel_direction_right=False,
        )
        == expected_account_rels
    )

    expected_lambda_rels = {
        (
            "arn:aws:events:us-east-1:123456789012:rule/hourly-lambda-trigger",
            "arn:aws:lambda:us-east-1:123456789012:function:ProcessHourlyJob",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "EventRule",
            "arn",
            "AWSLambda",
            "id",
            "TRIGGERS",
            rel_direction_right=True,
        )
        == expected_lambda_rels
    )
