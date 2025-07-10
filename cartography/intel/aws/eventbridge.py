import logging
from typing import Any
from typing import Dict
from typing import Tuple

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

# Map of target type name -> matcher function that returns True if an ARN matches the target type.
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
    "firehose_delivery_streams": lambda arn: ":firehose:" in arn and ":deliverystream/" in arn,
    "redshift_clusters": lambda arn: ":redshift:" in arn and ":cluster:" in arn,
}

@timeit
@aws_handle_regions
def get_event_rules(
    boto3_session: boto3.session.Session,
    region: str,
) -> dict[str, Any]:
    """Fetch EventBridge / CloudWatch Event rules and their targets for a single region.

    Required IAM permissions:
      - events:ListRules
      - events:ListTargetsByRule
    """
    client = boto3_session.client(
        "events", region_name=region, config=get_botocore_config()
    )

    rules: list[dict[str, Any]] = []
    targets_by_rule: dict[str, list[dict[str, Any]]] = {}

    paginator = client.get_paginator("list_rules")
    for page in paginator.paginate():
        rules.extend(page.get("Rules", []))

    for rule in rules:
        rule_name = rule["Name"]
        targets: list[dict[str, Any]] = []

        target_paginator = client.get_paginator("list_targets_by_rule")
        for page in target_paginator.paginate(Rule=rule_name):
            targets.extend(page.get("Targets", []))

        if targets:
            targets_by_rule[rule_name] = targets

    return {"Rules": rules, "Targets": targets_by_rule}

def classify_target_arn(arn: str) -> Tuple[str, str]:
    """Return a tuple of (target_type, arn). Unknown types are labelled 'unknown'."""
    for target_type, matcher in SUPPORTED_TARGET_TYPES.items():
        if matcher(arn):
            return target_type, arn
    return "unknown", arn

def classify_and_group_targets(targets: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Classify a list of EventBridge targets and group their ARNs by type.

    Only non-empty groups are returned.
    """
    groups: dict[str, list[str]] = {}
    unknown_targets: list[str] = []

    for target in targets:
        raw_arn = target.get("Arn", "").strip()
        if not raw_arn:
            continue

        target_type, arn = classify_target_arn(raw_arn)

        if target_type == "unknown":
            unknown_targets.append(arn)
            logger.debug("Unknown target type for ARN: %s", arn)
            continue

        field_name = f"{target_type}_arns"
        groups.setdefault(field_name, []).append(arn)

    if unknown_targets:
        groups["unknown_target_arns"] = unknown_targets

    return groups

def transform_event_rules(data: dict[str, Any], region: str) -> list[dict[str, Any]]:
    """Transform the raw AWS API response into the shape expected by EventRuleSchema.

    Target ARN lists are only included if non-empty.
    """
    transformed: list[dict[str, Any]] = []

    for rule in data["Rules"]:
        rule_name = rule["Name"]

        item: dict[str, Any] = {
            "Arn": rule["Arn"],
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

        targets = data["Targets"].get(rule_name, [])
        if targets:
            target_groups = classify_and_group_targets(targets)
            for field_name, arns in target_groups.items():
                item[field_name] = arns

            total_targets = len(targets)
            classified_targets = sum(
                len(arns)
                for key, arns in target_groups.items()
                if key != "unknown_target_arns"
            )
            if total_targets > classified_targets:
                stat_handler.incr(
                    "eventbridge.unknown_targets", total_targets - classified_targets
                )

        transformed.append(item)

    return transformed

def load_event_rules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """Load EventBridge rules into Neo4j using the generic load() helper."""
    logger.info(
        "Loading %d CloudWatch Event rules for region %s into graph.",
        len(data),
        region,
    )

    stat_handler.incr("eventbridge.rules.loaded", len(data))

    rules_with_targets = sum(
        1 for rule in data if any(key.endswith("_arns") for key in rule.keys())
    )
    stat_handler.incr("eventbridge.rules_with_targets", rules_with_targets)

    load(
        neo4j_session,
        EventRuleSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
    )

def cleanup_event_rules(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """Remove stale EventRule nodes from the graph."""
    logger.debug("Running CloudWatch Event rule cleanup job.")
    GraphJob.from_node_schema(EventRuleSchema(), common_job_parameters).run(neo4j_session)

@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """Entry-point called by the AWS ingestion pipeline."""
    for region in regions:
        logger.info(
            "Syncing CloudWatch Event rules for region %s in account %s.",
            region,
            current_aws_account_id,
        )

        raw_rules = get_event_rules(boto3_session, region)
        transformed_rules = transform_event_rules(raw_rules, region)

        load_event_rules(
            neo4j_session,
            transformed_rules,
            region,
            current_aws_account_id,
            update_tag,
        )

  
    cleanup_event_rules(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="EventRule",
        update_tag=update_tag,
        stat_handler=stat_handler,
    ) 

