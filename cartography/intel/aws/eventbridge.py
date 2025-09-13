import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.eventbridge.rule import EventBridgeRuleSchema
from cartography.models.aws.eventbridge.target import EventBridgeTargetSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_eventbridge_rules(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "events", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("list_rules")
    rules = []

    for page in paginator.paginate():
        rules.extend(page.get("Rules", []))

    return rules


@timeit
@aws_handle_regions
def get_eventbridge_targets(
    boto3_session: boto3.Session, region: str, rules: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "events", region_name=region, config=get_botocore_config()
    )
    targets = []
    for rule in rules:
        paginator = client.get_paginator("list_targets_by_rule")
        for page in paginator.paginate(Rule=rule["Name"]):
            for target in page.get("Targets", []):
                target["RuleArn"] = rule["Arn"]
                targets.append(target)
    return targets


def transform_eventbridge_targets(
    targets: List[Dict[str, Any]],
    region: str,
) -> List[Dict[str, Any]]:
    """
    Transform EventBridge target data for ingestion into Neo4j.
    """
    transformed_data = []
    for target in targets:
        transformed_target = {
            "Id": target["Arn"],
            "Arn": target["Arn"],
            "RuleArn": target["RuleArn"],
            "RoleArn": target.get("RoleArn"),
            "Region": region,
        }
        transformed_data.append(transformed_target)
    return transformed_data


@timeit
def load_eventbridge_rules(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading EventBridge {len(data)} rules for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        EventBridgeRuleSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_eventbridge_targets(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading EventBridge {len(data)} targets for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        EventBridgeTargetSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Running EventBridge cleanup job.")
    GraphJob.from_node_schema(EventBridgeRuleSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(EventBridgeTargetSchema(), common_job_parameters).run(
        neo4j_session
    )


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
        logger.info(
            f"Syncing EventBridge for region '{region}' in account '{current_aws_account_id}'.",
        )

        rules = get_eventbridge_rules(boto3_session, region)
        load_eventbridge_rules(
            neo4j_session,
            rules,
            region,
            current_aws_account_id,
            update_tag,
        )

        targets = get_eventbridge_targets(boto3_session, region, rules)
        transformed_targets = transform_eventbridge_targets(targets, region)
        load_eventbridge_targets(
            neo4j_session,
            transformed_targets,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
