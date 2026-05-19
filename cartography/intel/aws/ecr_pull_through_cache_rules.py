import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.ecr.pull_through_cache_rule import (
    ECRPullThroughCacheRuleSchema,
)
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_pull_through_cache_rules(
    boto3_session: boto3.session.Session,
    region: str,
    registry_id: str,
) -> List[Dict[str, Any]]:
    logger.debug(
        "Getting ECR pull through cache rules for registry '%s' in region '%s'.",
        registry_id,
        region,
    )
    client = create_boto3_client(boto3_session, "ecr", region_name=region)
    paginator = client.get_paginator("describe_pull_through_cache_rules")
    rules: List[Dict[str, Any]] = []
    for page in paginator.paginate(registryId=registry_id):
        rules.extend(page.get("pullThroughCacheRules", []))
    return rules


def transform_pull_through_cache_rules(
    rules: List[Dict[str, Any]],
    region: str,
) -> List[Dict[str, Any]]:
    transformed_rules = []
    for rule in rules:
        registry_id = rule["registryId"]
        ecr_repository_prefix = rule["ecrRepositoryPrefix"]
        transformed_rules.append(
            {
                "id": f"{registry_id}:{region}:{ecr_repository_prefix}",
                "registry_id": registry_id,
                "ecr_repository_prefix": ecr_repository_prefix,
                "upstream_registry_url": rule.get("upstreamRegistryUrl"),
                "upstream_registry": rule.get("upstreamRegistry"),
                "upstream_repository_prefix": rule.get("upstreamRepositoryPrefix"),
                "credential_arn": rule.get("credentialArn"),
                "custom_role_arn": rule.get("customRoleArn"),
                "created_at": rule.get("createdAt"),
                "updated_at": rule.get("updatedAt"),
            }
        )
    return transformed_rules


@timeit
def load_pull_through_cache_rules(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    logger.info(
        "Loading %d ECR pull through cache rules for registry '%s' in region '%s' into graph.",
        len(data),
        current_aws_account_id,
        region,
    )
    load(
        neo4j_session,
        ECRPullThroughCacheRuleSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    logger.debug("Running ECR pull through cache rule cleanup job.")
    GraphJob.from_node_schema(
        ECRPullThroughCacheRuleSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info(
            "Syncing ECR pull through cache rules for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        rules = get_pull_through_cache_rules(
            boto3_session,
            region,
            current_aws_account_id,
        )
        transformed_rules = transform_pull_through_cache_rules(rules, region)
        load_pull_through_cache_rules(
            neo4j_session,
            transformed_rules,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
