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
def test_sync_event_rules(mock_get_rules, neo4j_session):
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AWS_ID": TEST_ACCOUNT_ID,
    }

    neo4j_session.run(
        "MERGE (a:AWSAccount {id: $account_id}) SET a.lastupdated = $update_tag",
        account_id=TEST_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    for role in [
        "EventBridgeRole",
        "CrossAccountRole",
        "StepFunctionRole",
        "ECSTaskRole",
        "CodeBuildRole",
        "CodePipelineRole",
    ]:
        neo4j_session.run(
            "MERGE (r:AWSRole {arn: $arn})",
            arn=f"arn:aws:iam::{TEST_ACCOUNT_ID}:role/{role}",
        )

    service_mappings = [
        (":lambda:", ":function:", "AWSLambda", "id"),
        (":sns:", None, "SNSTopic", "arn"),
        (":sqs:", None, "SQSQueue", "arn"),
        (":states:", None, "StepFunction", "arn"),
        (":ecs:", "cluster/", "ECSCluster", "arn"),
        (":kinesis:", ":stream/", "KinesisStream", "arn"),
        (":codebuild:", ":project/", "CodeBuildProject", "arn"),
        (":codepipeline:", None, "CodePipeline", "arn"),
    ]

    for targets in MOCK_EVENT_RULES_RESPONSE["Targets"].values():
        for target in targets:
            arn = target["Arn"]
            for service, resource, label, id_field in service_mappings:
                if service in arn and (resource is None or resource in arn):
                    neo4j_session.run(
                        f"MERGE (n:{label} {{{id_field}: $arn}})", arn=arn
                    )
                    break

    sync(
        neo4j_session,
        None,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    expected_nodes = {
        (rule["Arn"], rule["Name"], rule["State"])
        for rule in MOCK_EVENT_RULES_RESPONSE["Rules"]
    }
    assert (
        check_nodes(neo4j_session, "EventRule", ["arn", "name", "state"])
        == expected_nodes
    )

    rule = neo4j_session.run(
        "MATCH (r:EventRule {name: 'hourly-batch-job'}) RETURN r"
    ).single()["r"]
    assert rule["schedule_expression"] == "rate(1 hour)"
    assert rule["description"] == "Triggers batch job every hour"
    assert rule["event_bus_name"] == "default"

    relationship_tests = [
        (
            "EventRule",
            "arn",
            "AWSAccount",
            "id",
            "RESOURCE",
            False,
            len(MOCK_EVENT_RULES_RESPONSE["Rules"]),
        ),
        ("EventRule", "arn", "AWSLambda", "id", "TRIGGERS", True, 2),
        ("EventRule", "arn", "SNSTopic", "arn", "PUBLISHES_TO", True, 1),
        ("EventRule", "arn", "SQSQueue", "arn", "SENDS_TO", True, 1),
        ("EventRule", "arn", "KinesisStream", "arn", "SENDS_TO", True, 1),
        ("EventRule", "arn", "StepFunction", "arn", "EXECUTES", True, 1),
        ("EventRule", "arn", "ECSCluster", "arn", "TARGETS", True, 1),
        ("EventRule", "arn", "CodeBuildProject", "arn", "TRIGGERS_BUILD", True, 1),
        ("EventRule", "arn", "CodePipeline", "arn", "STARTS_PIPELINE", True, 1),
        ("EventRule", "arn", "AWSRole", "arn", "USES_ROLE", True, 4),
    ]

    for (
        source_label,
        source_field,
        target_label,
        target_field,
        rel_type,
        direction,
        expected_count,
    ) in relationship_tests:
        rels = check_rels(
            neo4j_session,
            source_label,
            source_field,
            target_label,
            target_field,
            rel_type,
            rel_direction_right=direction,
        )
        assert (
            len(rels) == expected_count
        ), f"Expected {expected_count} {rel_type} relationships, got {len(rels)}"

    rel_prop = neo4j_session.run(
        """
        MATCH (r:EventRule {name: 'hourly-batch-job'})-[rel:TRIGGERS]->(l:AWSLambda)
        WHERE l.id = 'arn:aws:lambda:us-east-1:123456789012:function:ProcessBatchJob'
        RETURN rel.target_id as target_id
        """
    ).single()
    assert rel_prop["target_id"] == "1"

    unknown_count = neo4j_session.run(
        "MATCH (n) WHERE n.arn CONTAINS 'some-future-service' OR n.arn CONTAINS 'custom-service' RETURN count(n) as count"
    ).single()["count"]
    assert unknown_count == 0

    disabled = neo4j_session.run(
        "MATCH (r:EventRule {name: 'cross-account-events'}) RETURN r"
    ).single()["r"]
    assert disabled["state"] == "DISABLED"
    assert disabled["event_bus_name"] == "custom-event-bus"
    assert disabled["managed_by"] == "partner-service"
