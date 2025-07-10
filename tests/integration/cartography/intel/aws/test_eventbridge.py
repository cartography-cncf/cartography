from unittest.mock import patch

import cartography.intel.aws.eventbridge
from cartography.intel.aws.eventbridge import sync
from tests.data.aws.eventbridge.event_rules import MOCK_EVENT_RULES_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "123456789012"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 1234567890


@patch.object(
    cartography.intel.aws.eventbridge,
    "get_event_rules",
    return_value=MOCK_EVENT_RULES_RESPONSE,
)
def test_sync_event_rules_nodes(mock_get_rules, neo4j_session):
    """EventRule nodes are created with expected labels/properties."""
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID}

    sync(
        neo4j_session,
        boto3_session=None,
        regions=[TEST_REGION],
        current_aws_account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
        common_job_parameters=common_job_parameters,
    )

    expected_nodes = {
        (
            "arn:aws:events:us-east-1:123456789012:rule/hourly-batch-job",
            "hourly-batch-job",
            "ENABLED",
        ),
        (
            "arn:aws:events:us-east-1:123456789012:rule/ec2-state-change",
            "ec2-state-change",
            "ENABLED",
        ),
        (
            "arn:aws:events:us-east-1:123456789012:rule/cross-account-events",
            "cross-account-events",
            "DISABLED",
        ),
        (
            "arn:aws:events:us-east-1:123456789012:rule/codebuild-trigger",
            "codebuild-trigger",
            "ENABLED",
        ),
        (
            "arn:aws:events:us-east-1:123456789012:rule/pipeline-trigger",
            "pipeline-trigger",
            "ENABLED",
        ),
        (
            "arn:aws:events:us-east-1:123456789012:rule/api-gateway-trigger",
            "api-gateway-trigger",
            "ENABLED",
        ),
        (
            "arn:aws:events:us-east-1:123456789012:rule/unknown-target-test",
            "unknown-target-test",
            "ENABLED",
        ),
    }
    assert (
        check_nodes(neo4j_session, "EventRule", ["arn", "name", "state"])
        == expected_nodes
    )


@patch.object(
    cartography.intel.aws.eventbridge,
    "get_event_rules",
    return_value=MOCK_EVENT_RULES_RESPONSE,
)
def test_sync_event_rules_relationships_to_account(mock_get_rules, neo4j_session):
    """EventRule nodes link to AWSAccount via RESOURCE."""
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID}

    neo4j_session.run(
        """
        MERGE (a:AWSAccount {id: $account_id})
        SET a.lastupdated = $update_tag
        """,
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    sync(
        neo4j_session,
        None,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    expected = {
        (
            "arn:aws:events:us-east-1:123456789012:rule/hourly-batch-job",
            TEST_ACCOUNT_ID,
        ),
        (
            "arn:aws:events:us-east-1:123456789012:rule/ec2-state-change",
            TEST_ACCOUNT_ID,
        ),
        (
            "arn:aws:events:us-east-1:123456789012:rule/cross-account-events",
            TEST_ACCOUNT_ID,
        ),
        (
            "arn:aws:events:us-east-1:123456789012:rule/codebuild-trigger",
            TEST_ACCOUNT_ID,
        ),
        (
            "arn:aws:events:us-east-1:123456789012:rule/pipeline-trigger",
            TEST_ACCOUNT_ID,
        ),
        (
            "arn:aws:events:us-east-1:123456789012:rule/api-gateway-trigger",
            TEST_ACCOUNT_ID,
        ),
        (
            "arn:aws:events:us-east-1:123456789012:rule/unknown-target-test",
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
        == expected
    )


@patch.object(
    cartography.intel.aws.eventbridge,
    "get_event_rules",
    return_value=MOCK_EVENT_RULES_RESPONSE,
)
def test_sync_event_rules_relationships_to_targets(mock_get_rules, neo4j_session):
    """EventRule nodes link to their various targets."""
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID}

    neo4j_session.run(
        """
        MERGE (l1:AWSLambda {id: 'arn:aws:lambda:us-east-1:123456789012:function:ProcessBatchJob'})
        MERGE (l2:AWSLambda {id: 'arn:aws:lambda:us-east-1:123456789012:function:HandleEC2StateChange'})
        MERGE (sns:SNSTopic {arn: 'arn:aws:sns:us-east-1:123456789012:batch-notifications'})
        MERGE (sqs:SQSQueue {arn: 'arn:aws:sqs:us-east-1:123456789012:ec2-events-queue'})
        MERGE (sf:StepFunction {arn: 'arn:aws:states:us-east-1:123456789012:stateMachine:ProcessCrossAccountEvents'})
        MERGE (ks:KinesisStream {arn: 'arn:aws:kinesis:us-east-1:123456789012:stream/event-stream'})
        MERGE (ecs:ECSCluster {arn: 'arn:aws:ecs:us-east-1:123456789012:cluster/processing-cluster'})
        MERGE (cb:CodeBuildProject {arn: 'arn:aws:codebuild:us-east-1:123456789012:project/MyBuildProject'})
        MERGE (cp:CodePipeline {arn: 'arn:aws:codepipeline:us-east-1:123456789012:my-pipeline'})
        MERGE (api:APIGatewayRestAPI {id: 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/prod/POST/webhook'})
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

    expected_lambda = {
        (
            "arn:aws:events:us-east-1:123456789012:rule/hourly-batch-job",
            "arn:aws:lambda:us-east-1:123456789012:function:ProcessBatchJob",
        ),
        (
            "arn:aws:events:us-east-1:123456789012:rule/ec2-state-change",
            "arn:aws:lambda:us-east-1:123456789012:function:HandleEC2StateChange",
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
        == expected_lambda
    )

    expected_sns = {
        (
            "arn:aws:events:us-east-1:123456789012:rule/hourly-batch-job",
            "arn:aws:sns:us-east-1:123456789012:batch-notifications",
        )
    }
    assert (
        check_rels(
            neo4j_session,
            "EventRule",
            "arn",
            "SNSTopic",
            "arn",
            "PUBLISHES_TO",
            rel_direction_right=True,
        )
        == expected_sns
    )

    expected_sqs = {
        (
            "arn:aws:events:us-east-1:123456789012:rule/ec2-state-change",
            "arn:aws:sqs:us-east-1:123456789012:ec2-events-queue",
        )
    }
    assert (
        check_rels(
            neo4j_session,
            "EventRule",
            "arn",
            "SQSQueue",
            "arn",
            "SENDS_TO",
            rel_direction_right=True,
        )
        == expected_sqs
    )

    expected_cb = {
        (
            "arn:aws:events:us-east-1:123456789012:rule/codebuild-trigger",
            "arn:aws:codebuild:us-east-1:123456789012:project/MyBuildProject",
        )
    }
    assert (
        check_rels(
            neo4j_session,
            "EventRule",
            "arn",
            "CodeBuildProject",
            "arn",
            "TRIGGERS_BUILD",
            rel_direction_right=True,
        )
        == expected_cb
    )

    expected_cp = {
        (
            "arn:aws:events:us-east-1:123456789012:rule/pipeline-trigger",
            "arn:aws:codepipeline:us-east-1:123456789012:my-pipeline",
        )
    }
    assert (
        check_rels(
            neo4j_session,
            "EventRule",
            "arn",
            "CodePipeline",
            "arn",
            "STARTS_PIPELINE",
            rel_direction_right=True,
        )
        == expected_cp
    )

    expected_api = {
        (
            "arn:aws:events:us-east-1:123456789012:rule/api-gateway-trigger",
            "arn:aws:execute-api:us-east-1:123456789012:abcdef123/prod/POST/webhook",
        )
    }
    assert (
        check_rels(
            neo4j_session,
            "EventRule",
            "arn",
            "APIGatewayRestAPI",
            "id",
            "INVOKES_API",
            rel_direction_right=True,
        )
        == expected_api
    )
