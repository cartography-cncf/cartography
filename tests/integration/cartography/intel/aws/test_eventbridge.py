from unittest.mock import patch

import cartography.intel.aws.eventbridge
from cartography.intel.aws.eventbridge import sync

from tests.integration.util import check_nodes, check_rels

from tests.data.aws.eventbridge.event_rules import (
    MOCK_EVENT_RULES_RESPONSE,
)

TEST_ACCOUNT_ID = "123456789012"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 1234567890

@patch.object(cartography.intel.aws.eventbridge, "get_event_rules", return_value=MOCK_EVENT_RULES_RESPONSE)
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

    target_arns = set()
    for tgt_list in MOCK_EVENT_RULES_RESPONSE["Targets"].values():
        for tgt in tgt_list:
            target_arns.add(tgt["Arn"])

    for arn in target_arns:
        if ":lambda:" in arn and ":function:" in arn:
            node_label = "AWSLambda"
            id_field = "id"
        elif ":sns:" in arn:
            node_label = "SNSTopic"
            id_field = "arn"
        elif ":sqs:" in arn:
            node_label = "SQSQueue"
            id_field = "arn"
        elif ":states:" in arn:
            node_label = "StepFunction"
            id_field = "arn"
        elif ":ecs:" in arn and "cluster/" in arn:
            node_label = "ECSCluster"
            id_field = "arn"
        elif ":kinesis:" in arn and ":stream/" in arn:
            node_label = "KinesisStream"
            id_field = "arn"
        elif ":codebuild:" in arn and ":project/" in arn:
            node_label = "CodeBuildProject"
            id_field = "arn"
        elif ":codepipeline:" in arn:
            node_label = "CodePipeline"
            id_field = "arn"
        else:
            
            continue

        neo4j_session.run(
            f"MERGE (n:{node_label} {{{id_field}: $arn}})",
            arn=arn,
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
        (rule["Arn"], rule["Name"], rule["State"]) for rule in MOCK_EVENT_RULES_RESPONSE["Rules"]
    }
    assert (
        check_nodes(neo4j_session, "EventRule", ["arn", "name", "state"])
        == expected_nodes
    )

    expected_account_rels = {
        (rule["Arn"], TEST_ACCOUNT_ID) for rule in MOCK_EVENT_RULES_RESPONSE["Rules"]
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

    expected_lambda_rels = set()
    for rule_name, tgt_list in MOCK_EVENT_RULES_RESPONSE["Targets"].items():
        for tgt in tgt_list:
            if ":lambda:" in tgt["Arn"] and ":function:" in tgt["Arn"]:
                
                rule_arn = next(r["Arn"] for r in MOCK_EVENT_RULES_RESPONSE["Rules"] if r["Name"] == rule_name)
                expected_lambda_rels.add((rule_arn, tgt["Arn"]))

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

