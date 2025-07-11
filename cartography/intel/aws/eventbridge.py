import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.eventbridge.event_rule import EventRuleSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
@aws_handle_regions
def get_event_rules(session: boto3.session.Session, region: str) -> dict[str, Any]:
    client = session.client("events", region_name=region, config=get_botocore_config())

    rules: list[dict[str, Any]] = []
    for page in client.get_paginator("list_rules").paginate():
        rules.extend(page.get("Rules", []))

    targets_by_rule: dict[str, list[dict[str, Any]]] = {}
    for rule in rules:
        rule_name = rule["Name"]
        targets: list[dict[str, Any]] = []
        for page in client.get_paginator("list_targets_by_rule").paginate(
            Rule=rule_name
        ):
            targets.extend(page.get("Targets", []))
        if targets:
            targets_by_rule[rule_name] = targets

    return {"Rules": rules, "Targets": targets_by_rule}


def transform_event_rules(
    data: dict[str, Any],
    region: str,
) -> list[dict[str, Any]]:
    transformed_rules: list[dict[str, Any]] = []

    for rule in data["Rules"]:
        rule_name = rule["Name"]
        rule_arn = rule["Arn"]

        transformed_rule = {
            "arn": rule_arn,
            "name": rule_name,
            "state": rule.get("State"),
            "description": rule.get("Description"),
            "event_pattern": rule.get("EventPattern"),
            "schedule_expression": rule.get("ScheduleExpression"),
            "role_arn": rule.get("RoleArn"),
            "event_bus_name": rule.get("EventBusName", "default"),
            "managed_by": rule.get("ManagedBy"),
            "created_by": rule.get("CreatedBy"),
            "region": region,
            "_target_arns": [],
        }

        for target in data["Targets"].get(rule_name, []):
            transformed_rule["_target_arns"].append(
                {
                    "id": target["Id"],
                    "arn": target["Arn"],
                    "role_arn": target.get("RoleArn"),
                }
            )

        transformed_rules.append(transformed_rule)

    return transformed_rules


def load_event_rules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        EventRuleSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
    )


def _create_target_relationships(
    neo4j_session: neo4j.Session,
    rules_data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    for rule in rules_data:
        rule_arn = rule["arn"]

        for target in rule.get("_target_arns", []):
            target_arn = target["arn"]

            if ":lambda:" in target_arn and ":function:" in target_arn:
                neo4j_session.run(
                    """
                    MATCH (rule:EventRule {arn: $rule_arn})
                    MATCH (lambda:AWSLambda {id: $target_arn})
                    MERGE (rule)-[r:TRIGGERS {lastupdated: $update_tag}]->(
                        lambda
                    )
                    SET r.target_id = $target_id,
                        r.target_role_arn = $target_role_arn
                    """,
                    rule_arn=rule_arn,
                    target_arn=target_arn,
                    target_id=target["id"],
                    target_role_arn=target.get("role_arn"),
                    update_tag=update_tag,
                )

            elif ":sns:" in target_arn:
                neo4j_session.run(
                    """
                    MATCH (rule:EventRule {arn: $rule_arn})
                    MATCH (topic:SNSTopic {arn: $target_arn})
                    MERGE (rule)-[r:PUBLISHES_TO {lastupdated: $update_tag}]->(
                        topic
                    )
                    SET r.target_id = $target_id
                    """,
                    rule_arn=rule_arn,
                    target_arn=target_arn,
                    target_id=target["id"],
                    update_tag=update_tag,
                )

            elif ":sqs:" in target_arn:
                neo4j_session.run(
                    """
                    MATCH (rule:EventRule {arn: $rule_arn})
                    MATCH (queue:SQSQueue {arn: $target_arn})
                    MERGE (rule)-[r:SENDS_TO {lastupdated: $update_tag}]->(
                        queue
                    )
                    SET r.target_id = $target_id
                    """,
                    rule_arn=rule_arn,
                    target_arn=target_arn,
                    target_id=target["id"],
                    update_tag=update_tag,
                )

            elif ":states:" in target_arn:
                neo4j_session.run(
                    """
                    MATCH (rule:EventRule {arn: $rule_arn})
                    MATCH (sf:StepFunction {arn: $target_arn})
                    MERGE (rule)-[r:EXECUTES {lastupdated: $update_tag}]->(sf)
                    SET r.target_id = $target_id
                    """,
                    rule_arn=rule_arn,
                    target_arn=target_arn,
                    target_id=target["id"],
                    update_tag=update_tag,
                )

            elif ":ecs:" in target_arn and "cluster/" in target_arn:
                # ECS Cluster target
                neo4j_session.run(
                    """
                    MATCH (rule:EventRule {arn: $rule_arn})
                    MATCH (ecs:ECSCluster {arn: $target_arn})
                    MERGE (rule)-[r:TARGETS {lastupdated: $update_tag}]->(ecs)
                    SET r.target_id = $target_id
                    """,
                    rule_arn=rule_arn,
                    target_arn=target_arn,
                    target_id=target["id"],
                    update_tag=update_tag,
                )

            elif ":kinesis:" in target_arn and ":stream/" in target_arn:
                # Kinesis Stream target
                neo4j_session.run(
                    """
                    MATCH (rule:EventRule {arn: $rule_arn})
                    MATCH (stream:KinesisStream {arn: $target_arn})
                    MERGE (rule)-[r:SENDS_TO {lastupdated: $update_tag}]->(stream)
                    SET r.target_id = $target_id
                    """,
                    rule_arn=rule_arn,
                    target_arn=target_arn,
                    target_id=target["id"],
                    update_tag=update_tag,
                )

            elif ":codebuild:" in target_arn and ":project/" in target_arn:
                # CodeBuild Project target
                neo4j_session.run(
                    """
                    MATCH (rule:EventRule {arn: $rule_arn})
                    MATCH (proj:CodeBuildProject {arn: $target_arn})
                    MERGE (rule)-[r:TRIGGERS_BUILD {lastupdated: $update_tag}]->(proj)
                    SET r.target_id = $target_id
                    """,
                    rule_arn=rule_arn,
                    target_arn=target_arn,
                    target_id=target["id"],
                    update_tag=update_tag,
                )

            elif ":codepipeline:" in target_arn:
                # CodePipeline target
                neo4j_session.run(
                    """
                    MATCH (rule:EventRule {arn: $rule_arn})
                    MATCH (pipe:CodePipeline {arn: $target_arn})
                    MERGE (rule)-[r:STARTS_PIPELINE {lastupdated: $update_tag}]->(pipe)
                    SET r.target_id = $target_id
                    """,
                    rule_arn=rule_arn,
                    target_arn=target_arn,
                    target_id=target["id"],
                    update_tag=update_tag,
                )


def _create_role_relationships(
    neo4j_session: neo4j.Session,
    rules_data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    for rule in rules_data:
        if rule.get("role_arn"):
            neo4j_session.run(
                """
                MATCH (rule:EventRule {arn: $rule_arn})
                MATCH (role:AWSRole {arn: $role_arn})
                MERGE (rule)-[r:USES_ROLE {lastupdated: $update_tag}]->(role)
                """,
                rule_arn=rule["arn"],
                role_arn=rule["role_arn"],
                update_tag=update_tag,
            )


def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    logger.debug("Running EventBridge cleanup job")
    GraphJob.from_node_schema(EventRuleSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            f"Syncing EventBridge for account {current_aws_account_id} in {region}"
        )

        data = get_event_rules(boto3_session, region)

        transformed_rules = transform_event_rules(data, region)

        load_event_rules(
            neo4j_session,
            transformed_rules,
            region,
            current_aws_account_id,
            update_tag,
        )

        _create_target_relationships(neo4j_session, transformed_rules, update_tag)
        _create_role_relationships(neo4j_session, transformed_rules, update_tag)

    cleanup(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="EventRule",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
