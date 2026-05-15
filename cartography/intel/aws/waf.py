import logging
import time
from typing import *
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import EndpointConnectionError
from cloudconsolelink.clouds.aws import AWSLinker

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
@aws_handle_regions
def get_waf_classic_regional_web_acls(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    """
    Get WAF Classic Web ACLs for a specific region (for ALBs, etc.).
    """
    web_acls = []
    try:
        client = boto3_session.client('waf-regional', region_name=region)
        resp = client.list_web_acls()
        for acl in resp.get('WebACLs', []):
            acl['region'] = region
            web_acls.append(acl)

        while resp.get("NextMarker"):
            resp = client.list_web_acls(
                NextMarker=resp.get("NextMarker"),
            )
            for acl in resp.get('WebACLs', []):
                acl['region'] = region
                web_acls.append(acl)

    except EndpointConnectionError as e:
        logger.debug(f"WAF Regional is not supported in {region}: {e}")

    except ConnectTimeoutError as e:
        logger.debug(f"Connection to WAF Regional timed out in {region}: {e}")

    except ClientError as e:
        logger.error(f"Failed to list WAF Classic regional Web ACLs in {region}: {e}")

    return web_acls


@timeit
def get_waf_classic_global_web_acls(boto3_session: boto3.session.Session) -> List[Dict]:
    """
    Get WAF Classic Web ACLs for the global scope (for CloudFront).
    This should only be called once, not for every region.
    """
    web_acls = []
    try:
        client = boto3_session.client('waf', region_name='us-east-1')
        paginator = client.get_paginator('list_web_acls')
        for page in paginator.paginate():
            for acl in page.get('WebACLs', []):
                acl['region'] = 'global'
                web_acls.append(acl)
        return web_acls
    except ClientError as e:
        logger.error(f"Failed to call WAF Classic Global list_web_acls: {e}")
        return web_acls


@timeit
def get_waf_classic_details(boto3_session: boto3.session.Session, web_acl: Dict) -> Dict:
    """
    Gets detailed information for a given Web ACL. It determines whether to use
    the 'waf' or 'waf-regional' client based on the ACL's region tag.
    Now extracts additional details to align with WAFv2 ingestion.
    """
    web_acl_id = web_acl.get("WebACLId")
    region = web_acl.get("region")

    try:
        if region == 'global':
            client = boto3_session.client('waf', region_name='us-east-1')
            scope = 'CLOUDFRONT'
        else:
            client = boto3_session.client('waf-regional', region_name=region)
            scope = 'REGIONAL'

        response = client.get_web_acl(WebACLId=web_acl_id)
        details = response.get("WebACL", {})

        if not details:
            return {}

        # Add new details directly to the web_acl dictionary
        web_acl['arn'] = details.get("WebACLArn")
        web_acl['default_action'] = details.get("DefaultAction", {}).get("Type")
        web_acl['rules_count'] = len(details.get("Rules", []))
        web_acl['metric_name'] = details.get("MetricName")
        web_acl['scope'] = scope
        return web_acl

    except EndpointConnectionError as e:
        logger.debug(f"WAF Regional is not supported in {region}: {e}")

    except ConnectTimeoutError as e:
        logger.debug(f"Connection to WAF Regional timed out in {region}: {e}")

    except ClientError as e:
        logger.error(f"Error retrieving Web ACL details for {web_acl_id} in region {region}: {e}")
        return {}


@timeit
def transform_waf_classic_web_acls(boto3_session: boto3.session.Session, web_acls: List[Dict]) -> List[Dict]:
    transformed_acls = []
    for web_acl in web_acls:
        # get_waf_classic_details now returns the fully enriched object
        detailed_acl = get_waf_classic_details(boto3_session, web_acl.copy())

        # Ensure we have a valid, enriched ACL with an ARN before adding it
        if detailed_acl and detailed_acl.get("arn"):
            detailed_acl['consolelink'] = aws_console_link.get_console_link(arn=detailed_acl['arn'])
            transformed_acls.append(detailed_acl)

    return transformed_acls


def load_waf_classic_web_acls(session: neo4j.Session, web_acls: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.execute_write(_load_waf_classic_web_acls_tx, web_acls, current_aws_account_id, aws_update_tag)


@timeit
def _load_waf_classic_web_acls_tx(tx: neo4j.Transaction, web_acls: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    query: str = """
    UNWIND $Records as record
    WITH record WHERE record.arn IS NOT NULL
    MERGE (web_acl:AWSWAFClassicWebACL{id: record.arn})
    ON CREATE SET web_acl.firstseen = timestamp(),
        web_acl.arn = record.arn
    SET web_acl.lastupdated = $aws_update_tag,
        web_acl.name = record.Name,
        web_acl.region = record.region,
        web_acl.consolelink = record.consolelink,
        web_acl.scope = record.scope,
        web_acl.default_action = record.default_action,
        web_acl.rules_count = record.rules_count,
        web_acl.metric_name = record.metric_name
    WITH web_acl
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(web_acl)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        query,
        Records=web_acls,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_waf_classic_web_acls(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_waf_classic_web_acls_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_waf_classic(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    """
    Syncs both regional and global WAF Classic ACLs.
    """
    all_web_acls = []

    global_acls = get_waf_classic_global_web_acls(boto3_session)
    all_web_acls.extend(global_acls)

    for region in regions:
        regional_acls = get_waf_classic_regional_web_acls(boto3_session, region)
        all_web_acls.extend(regional_acls)

    if not all_web_acls:
        return

    logger.info(f"Found {len(all_web_acls)} total WAF Classic WebACLs (global and regional).")
    transformed_acls = transform_waf_classic_web_acls(boto3_session, all_web_acls)

    load_waf_classic_web_acls(neo4j_session, transformed_acls, current_aws_account_id, update_tag)

    cleanup_waf_classic_web_acls(neo4j_session, common_job_parameters)


@timeit
def get_waf_v2_web_acl_details(
    client: boto3.client, acl: Dict, scope: str, region: str,
) -> Dict:
    """
    Get detailed information about a WAFv2 Web ACL
    """
    try:
        response = client.get_web_acl(Name=acl["Name"], Scope=scope, Id=acl["Id"])
        acl_details = response.get("WebACL", {})

        return {
            "Name": acl.get("Name", ""),
            "Id": acl.get("Id", ""),
            "ARN": acl.get("ARN", ""),
            "region": region,
            "scope": scope,
            "default_action": acl_details.get("DefaultAction", {}).get("Type", ""),
            "rules_count": str(len(acl_details.get("Rules", []))),
            "capacity": str(acl_details.get("Capacity", 0)),
        }
    except ClientError as e:
        logger.error(
            f'Failed to get WAF ACL details for {acl.get("Name", "Unknown")}: {e}',
        )
        return {}


@timeit
def get_waf_v2_global_acls(boto3_session: boto3.session.Session) -> List[Dict]:
    """
    Get WAFv2 Web ACLs for the global scope (CloudFront).
    Should only be called once, not for every region.
    """
    client = boto3_session.client("wafv2", region_name="us-east-1")
    return get_waf_v2_web_acls_for_scope(client, "CLOUDFRONT", "global")


@timeit
def get_waf_v2_regional_acls(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    """
    Get WAFv2 Web ACLs for a specific region.
    """
    regional_client = boto3_session.client("wafv2", region_name=region)
    return get_waf_v2_web_acls_for_scope(
        regional_client, "REGIONAL", region,
    )


@timeit
@aws_handle_regions
def get_waf_v2_web_acls_for_scope(
    client: boto3.client, scope: str, region: str,
) -> List[Dict]:
    web_acls = []
    try:
        resp = client.list_web_acls(Scope=scope)
        for acl in resp.get("WebACLs", []):
            acl_with_details = get_waf_v2_web_acl_details(client, acl, scope, region)
            if acl_with_details:
                web_acls.append(acl_with_details)
        while resp.get("NextMarker"):
            resp = client.list_web_acls(
                Scope=scope,
                NextMarker=resp.get("NextMarker"),
            )
            for acl in resp.get("WebACLs", []):
                acl_with_details = get_waf_v2_web_acl_details(client, acl, scope, region)
                if acl_with_details:
                    web_acls.append(acl_with_details)
    except ClientError as e:
        logger.error(f"Failed to list WAF v2 ACLs for scope {scope} in {region}: {e}")
    return web_acls


@timeit
def transform_waf_v2_web_acls(web_acls: List[Dict]) -> List[Dict]:
    transformed_acls = []
    for web_acl in web_acls:
        web_acl["arn"] = web_acl["ARN"]
        web_acl["consolelink"] = aws_console_link.get_console_link(arn=web_acl['arn'])
        transformed_acls.append(web_acl)
    return transformed_acls


def load_waf_v2_web_acls(session: neo4j.Session, web_acls: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.execute_write(_load_waf_v2_web_acls_tx, web_acls, current_aws_account_id, aws_update_tag)


@timeit
def _load_waf_v2_web_acls_tx(tx: neo4j.Transaction, web_acls: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    query: str = """
    UNWIND $Records as record
    MERGE (web_acl:AWSWAFv2WebACL{id: record.arn})
    ON CREATE SET web_acl.firstseen = timestamp(),
        web_acl.arn = record.arn
    SET web_acl.lastupdated = $aws_update_tag,
        web_acl.name = record.Name,
        web_acl.region = record.region,
        web_acl.consolelink = record.consolelink,
        web_acl.scope = record.scope,
        web_acl.default_action = record.default_action,
        web_acl.rules_count = record.rules_count,
        web_acl.capacity = record.capacity
    WITH web_acl
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(web_acl)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        query,
        Records=web_acls,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_waf_v2_web_acls(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_waf_v2_web_acls_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_waf_v2(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    # 1. Call the global function ONCE
    all_web_acls = get_waf_v2_global_acls(boto3_session)

    # 2. Loop through regions for regional resources
    for region in regions:
        all_web_acls.extend(get_waf_v2_regional_acls(boto3_session, region))

    logger.info(f"Total WAF v2 WebACLs: {len(all_web_acls)}")
    if not all_web_acls:
        return

    # 3. No de-duplication is needed
    transformed_acls = transform_waf_v2_web_acls(all_web_acls)
    load_waf_v2_web_acls(neo4j_session, transformed_acls, current_aws_account_id, update_tag)
    cleanup_waf_v2_web_acls(neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing WAF for account '%s', at %s.", current_aws_account_id, tic)

    try:
        sync_waf_classic(neo4j_session, boto3_session, regions, current_aws_account_id, update_tag, common_job_parameters)

        sync_waf_v2(neo4j_session, boto3_session, regions, current_aws_account_id, update_tag, common_job_parameters)

    except Exception as ex:
        logger.error("failed to process waf - %s", ex)

    toc = time.perf_counter()
    logger.info(f"Time to process WAF: {toc - tic:0.4f} seconds")
