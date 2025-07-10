import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.eventbridge.event_rule import EventRuleSchema
from cartography.models.aws.eventbridge.event_target import EventTargetSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

SUPPORTED_TARGET_TYPES: Dict[str, Any] = {
    "lambda_functions": lambda arn: ":lambda:" in arn and ":function:" in arn,
    "sns_topics": lambda arn: ":sns:" in arn,
    "sqs_queues": lambda arn: ":sqs:" in arn,
    "ecs_clusters": lambda arn: ":ecs:" in arn and "cluster/" in arn,
    "step_functions": lambda arn: ":states:" in arn,
    "kinesis_streams": lambda arn: ":kinesis:" in arn and ":stream/" in arn,
    "codebuild_projects": lambda arn: ":codebuild:" in arn and ":project/" in arn,
    "codepipelines": lambda arn: ":codepipeline:" in arn,
    "api_gateways": lambda arn: ":execute-api:" in arn,
    "cloudwatch_log_groups": lambda arn: ":logs:" in arn and ":log-group:" in arn,
    "batch_job_queues": lambda arn: ":batch:" in arn and ":job-queue/" in arn,
    "sagemaker_pipelines": lambda arn: ":sagemaker:" in arn and ":pipeline/" in arn,
    "firehose_delivery_streams": lambda arn: ":firehose:" in arn
    and ":deliverystream/" in arn,
    "redshift_clusters": lambda arn: ":redshift:" in arn and ":cluster:" in arn,
}


@timeit
@aws_handle_regions
def get_event_rules(session: boto3.session.Session, region: str) -> dict[str, Any]:
    client = session.client("events", region_name=region, config=get_botocore_config())
    rules: List[Dict[str, Any]] = []
    targets_by_rule: Dict[str, List[Dict[str, Any]]] = {}
    for page in client.get_paginator("list_rules").paginate():
        rules.extend(page.get("Rules", []))
    for rule in rules:
        rule_name = rule["Name"]
        targets: List[Dict[str, Any]] = []
        for page in client.get_paginator("list_targets_by_rule").paginate(
            Rule=rule_name
        ):
            targets.extend(page.get("Targets", []))
        if targets:
            targets_by_rule[rule_name] = targets
    return {"Rules": rules, "Targets": targets_by_rule}


def classify_target_arn(arn: str) -> Tuple[str, str]:
    for t, f in SUPPORTED_TARGET_TYPES.items():
        if f(arn):
            return t, arn
    return "unknown", arn


def transform(
    data: dict[str, Any], region: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    rules_out: List[Dict[str, Any]] = []
    targets_out: List[Dict[str, Any]] = []
    for rule in data["Rules"]:
        rule_name = rule["Name"]
        rule_arn = rule["Arn"]
        rules_out.append(
            {
                "Arn": rule_arn,
                "Name": rule_name,
                "State": rule.get("State"),
                "Description": rule.get("Description"),
                "EventPattern": rule.get("EventPattern"),
                "ScheduleExpression": rule.get("ScheduleExpression"),
                "RoleArn": rule.get("RoleArn"),
                "EventBusName": rule.get("EventBusName", "default"),
                "ManagedBy": rule.get("ManagedBy"),
                "CreatedBy": rule.get("CreatedBy"),
                "Region": region,
            }
        )
        for tgt in data["Targets"].get(rule_name, []):
            targets_out.append(
                {
                    "id": f"{rule_arn}#{tgt['Id']}",
                    "Id": tgt["Id"],
                    "Arn": tgt["Arn"],
                    "RuleArn": rule_arn,
                    "RoleArn": tgt.get("RoleArn"),
                    "Input": tgt.get("Input"),
                    "InputPath": tgt.get("InputPath"),
                    "Region": region,
                }
            )
    return rules_out, targets_out


def _create_service_rels(
    sess: neo4j.Session, targets: List[Dict[str, Any]], tag: int
) -> None:
    mapping = {
        "lambda_functions": ("AWSLambda", "id"),
        "sns_topics": ("SNSTopic", "arn"),
        "sqs_queues": ("SQSQueue", "arn"),
        "kinesis_streams": ("KinesisStream", "arn"),
        "ecs_clusters": ("ECSCluster", "arn"),
        "step_functions": ("StepFunction", "arn"),
        "cloudwatch_log_groups": ("CloudWatchLogGroup", "arn"),
        "batch_job_queues": ("BatchJobQueue", "arn"),
        "sagemaker_pipelines": ("SageMakerPipeline", "arn"),
        "firehose_delivery_streams": ("FirehoseDeliveryStream", "arn"),
        "redshift_clusters": ("RedshiftCluster", "arn"),
        "codebuild_projects": ("CodeBuildProject", "arn"),
        "codepipelines": ("CodePipeline", "arn"),
        "api_gateways": ("APIGatewayRestAPI", "id"),
    }
    rel_labels = {
        "lambda_functions": "TRIGGERS",
        "sns_topics": "PUBLISHES_TO",
        "sqs_queues": "SENDS_TO",
        "kinesis_streams": "SENDS_TO",
        "ecs_clusters": "TARGETS",
        "step_functions": "EXECUTES",
        "cloudwatch_log_groups": "LOGS_TO",
        "batch_job_queues": "SUBMITS_TO",
        "sagemaker_pipelines": "STARTS_PIPELINE",
        "firehose_delivery_streams": "DELIVERS_TO",
        "redshift_clusters": "TARGETS",
        "codebuild_projects": "TRIGGERS_BUILD",
        "codepipelines": "STARTS_PIPELINE",
        "api_gateways": "INVOKES_API",
    }
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for t in targets:
        t_type, _ = classify_target_arn(t["Arn"])
        if t_type in mapping:
            grouped.setdefault(t_type, []).append(
                {"rarn": t["RuleArn"], "sarn": t["Arn"]}
            )
    for t_type, pairs in grouped.items():
        label, field = mapping[t_type]
        rel = rel_labels[t_type]
        sess.run(
            f"UNWIND $pairs as p MATCH (er:EventRule {{arn: p.rarn}}) MATCH (s:{label} {{{field}: p.sarn}}) MERGE (er)-[r:{rel} {{lastupdated:$tag}}]->(s)",
            pairs=pairs,
            tag=tag,
        )


def load_data(
    sess: neo4j.Session,
    rules: List[Dict[str, Any]],
    targets: List[Dict[str, Any]],
    region: str,
    aid: str,
    tag: int,
) -> None:
    load(sess, EventRuleSchema(), rules, lastupdated=tag, Region=region, AWS_ID=aid)
    load(sess, EventTargetSchema(), targets, lastupdated=tag, Region=region, AWS_ID=aid)
    _create_service_rels(sess, targets, tag)


def cleanup(sess: neo4j.Session, params: Dict[str, Any]) -> None:
    GraphJob.from_node_schema(EventRuleSchema(), params).run(sess)
    GraphJob.from_node_schema(EventTargetSchema(), params).run(sess)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    for region in regions:
        raw = get_event_rules(boto3_session, region)
        rules, targets = transform(raw, region)
        load_data(
            neo4j_session, rules, targets, region, current_aws_account_id, update_tag
        )
    cleanup(neo4j_session, common_job_parameters)
    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="EventRule",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
