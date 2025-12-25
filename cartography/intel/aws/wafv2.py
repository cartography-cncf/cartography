import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.wafv2 import AWSWAFv2RuleGroupSchema
from cartography.models.aws.wafv2 import AWSWAFv2WebACLSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_web_acls(boto3_session: boto3.Session, region: str) -> List[Dict[str, Any]]:
    client = boto3_session.client("wafv2", region_name=region)
    web_acls = []
    # Sync Regional Scope
    paginator = client.get_paginator("list_web_acls")
    for page in paginator.paginate(Scope="REGIONAL"):
        web_acls.extend(page["WebACLs"])

    # Sync CloudFront Scope (Global) - only from us-east-1 to avoid duplicates
    if region == "us-east-1":
        try:
            for page in paginator.paginate(Scope="CLOUDFRONT"):
                web_acls.extend(page["WebACLs"])
        except Exception as e:
            logger.warning(
                f"Failed to list WAFv2 WebACLs for CLOUDFRONT scope in {region}: {e}"
            )

    return web_acls


@timeit
@aws_handle_regions
def get_rule_groups(boto3_session: boto3.Session, region: str) -> List[Dict[str, Any]]:
    client = boto3_session.client("wafv2", region_name=region)
    rule_groups = []
    # Sync Regional Scope
    paginator = client.get_paginator("list_rule_groups")
    for page in paginator.paginate(Scope="REGIONAL"):
        rule_groups.extend(page["RuleGroups"])

    # Sync CloudFront Scope (Global) - only from us-east-1
    if region == "us-east-1":
        try:
            for page in paginator.paginate(Scope="CLOUDFRONT"):
                rule_groups.extend(page["RuleGroups"])
        except Exception as e:
            logger.warning(
                f"Failed to list WAFv2 RuleGroups for CLOUDFRONT scope in {region}: {e}"
            )

    return rule_groups


def transform_web_acls(web_acls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # No specific date conversion needed as 'list' output usually doesn't have dates,
    # but let's check if we need to describe them to get details.
    # ListWebACLs returns summary. DescribeWebACL returns full details.
    # user request probably is happy with summary nodes for now.
    return web_acls


def transform_rule_groups(rule_groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return rule_groups


@timeit
def load_web_acls(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSWAFv2WebACLSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_rule_groups(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSWAFv2RuleGroupSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.info("Running AWS WAFv2 cleanup")
    GraphJob.from_node_schema(AWSWAFv2WebACLSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(AWSWAFv2RuleGroupSchema(), common_job_parameters).run(
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
            f"Syncing AWS WAFv2 for region '{region}' in account '{current_aws_account_id}'."
        )

        web_acls = get_web_acls(boto3_session, region)
        web_acls = transform_web_acls(web_acls)
        load_web_acls(
            neo4j_session, web_acls, region, current_aws_account_id, update_tag
        )

        rule_groups = get_rule_groups(boto3_session, region)
        rule_groups = transform_rule_groups(rule_groups)
        load_rule_groups(
            neo4j_session, rule_groups, region, current_aws_account_id, update_tag
        )

    cleanup(neo4j_session, common_job_parameters)
