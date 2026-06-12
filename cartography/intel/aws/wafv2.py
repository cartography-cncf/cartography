import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.models.aws.wafv2 import AWSWebACLSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

# CLOUDFRONT-scoped web ACLs are global and can only be listed via us-east-1.
CLOUDFRONT_SCOPE_REGION = "us-east-1"


def _list_web_acls(client: Any, scope: str) -> List[Dict[str, Any]]:
    """
    List WAFv2 web ACLs for the given scope.

    WAFv2 does not provide a paginator for list_web_acls, so we paginate
    manually with NextMarker.
    """
    web_acls: List[Dict[str, Any]] = []
    next_marker = None
    while True:
        params: Dict[str, Any] = {"Scope": scope}
        if next_marker:
            params["NextMarker"] = next_marker
        page = client.list_web_acls(**params)
        page_acls = page.get("WebACLs", [])
        web_acls.extend(page_acls)
        next_marker = page.get("NextMarker")
        if not next_marker or not page_acls:
            break
    return web_acls


def _get_alb_arns_for_web_acl(client: Any, web_acl_arn: str) -> List[str]:
    response = client.list_resources_for_web_acl(
        WebACLArn=web_acl_arn,
        ResourceType="APPLICATION_LOAD_BALANCER",
    )
    return response.get("ResourceArns", [])


@timeit
@aws_handle_regions
def get_web_acls(
    boto3_session: boto3.session.Session,
    region: str,
    scope: str,
) -> List[Dict[str, Any]]:
    """
    Get WAFv2 web ACLs for the given scope, including the ARNs of the
    application load balancers each REGIONAL web ACL protects.

    API Gateway stages and CloudFront distributions are not fetched here:
    their nodes already carry the associated web ACL ARN (webaclarn and
    web_acl_id respectively), so those relationships are resolved at load
    time by matching on existing node properties.
    """
    client = create_boto3_client(
        boto3_session,
        "wafv2",
        region_name=region,
        config=get_botocore_config(),
    )
    web_acls = _list_web_acls(client, scope)
    if scope == "REGIONAL":
        for web_acl in web_acls:
            web_acl["AlbArns"] = _get_alb_arns_for_web_acl(client, web_acl["ARN"])
    return web_acls


def transform_web_acls(
    web_acls: List[Dict[str, Any]],
    scope: str,
) -> List[Dict[str, Any]]:
    transformed: List[Dict[str, Any]] = []
    for web_acl in web_acls:
        transformed.append(
            {
                "ARN": web_acl["ARN"],
                "Id": web_acl["Id"],
                "Name": web_acl.get("Name"),
                "Description": web_acl.get("Description"),
                "Scope": scope,
                "AlbArns": web_acl.get("AlbArns", []),
            }
        )
    return transformed


@timeit
def load_web_acls(
    neo4j_session: neo4j.Session,
    web_acl_data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        "Loading %d WAFv2 web ACLs for region '%s' into graph.",
        len(web_acl_data),
        region,
    )
    load(
        neo4j_session,
        AWSWebACLSchema(),
        web_acl_data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Running WAFv2 cleanup job.")
    cleanup_job = GraphJob.from_node_schema(
        AWSWebACLSchema(),
        common_job_parameters,
    )
    cleanup_job.run(neo4j_session)


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
            "Syncing WAFv2 regional web ACLs for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        regional_acls = get_web_acls(boto3_session, region, "REGIONAL")
        load_web_acls(
            neo4j_session,
            transform_web_acls(regional_acls, "REGIONAL"),
            region,
            current_aws_account_id,
            update_tag,
        )

    logger.info(
        "Syncing WAFv2 CloudFront-scoped web ACLs in account '%s'.",
        current_aws_account_id,
    )
    cloudfront_acls = get_web_acls(
        boto3_session,
        CLOUDFRONT_SCOPE_REGION,
        "CLOUDFRONT",
    )
    load_web_acls(
        neo4j_session,
        transform_web_acls(cloudfront_acls, "CLOUDFRONT"),
        CLOUDFRONT_SCOPE_REGION,
        current_aws_account_id,
        update_tag,
    )

    cleanup(neo4j_session, common_job_parameters)
