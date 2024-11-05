import logging
from typing import Dict
from typing import List

import boto3
import botocore
import neo4j

from cartography.util import aws_handle_regions
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_load_waf_resources(client: botocore.client.BaseClient,
                           elbv2_client: botocore.client.BaseClient, acl_arn: str) -> Dict[str, List[str]]:
    resources: Dict[str, List[str]] = {'ALBs': [], 'APIGWs': []}
    resources["APIGWs"].extend(
        client.list_resources_for_web_acl(WebACLArn=acl_arn, ResourceType='API_GATEWAY')['ResourceArns'])

    paginator = elbv2_client.get_paginator('describe_load_balancers')
    albs = client.list_resources_for_web_acl(WebACLArn=acl_arn, ResourceType='APPLICATION_LOAD_BALANCER')[
        'ResourceArns']
    for page in paginator.paginate(LoadBalancerArns=albs):
        for lb in page['LoadBalancers']:
            resources["ALBs"].append(lb['DNSName'])

    return resources


@timeit
def get_waf_acls(boto3_session: boto3.Session) -> List[Dict]:
    wafv2_client = boto3_session.client('wafv2', config=get_botocore_config())
    elbv2_client = boto3_session.client('elbv2', config=get_botocore_config())

    acls: List[Dict] = []
    for base_acl in wafv2_client.list_web_acls(Scope='REGIONAL')['WebACLs']:
        acl = wafv2_client.get_web_acl(Name=base_acl['Name'], Scope='REGIONAL', Id=base_acl['Id'])['WebACL']
        acl['Resources'] = get_load_waf_resources(wafv2_client, elbv2_client, acl['ARN'])
        acls.append(acl)

    return acls


@timeit
def load_waf_acl_alb_resources(neo4j_session, alb_ids: List[str], acl_id, current_aws_account_id, update_tag):
    ingest_resources = """
    UNWIND $ALB_IDS AS _ALB_ID
    MATCH (acl:WAFv2WebACL{id: $ACL_ID}), (alb:LoadBalancerV2{id: _ALB_ID})
    MERGE (acl)-[r:ASSOCIATED_WITH]->(alb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UPDATE_TAG
    WITH alb
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(alb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UPDATE_TAG
    """
    neo4j_session.run(
        ingest_resources,
        ACL_ID=acl_id,
        ALB_IDS=alb_ids,
        UPDATE_TAG=update_tag,
        AWS_ACCOUNT_ID=current_aws_account_id,
    )


@timeit
def load_waf_acl_apigw_resources(neo4j_session, apigw_arns, acl_id, update_tag):
    ingest_resources = """
    UNWIND $APIGW_IDS AS _APIGW_ID
    MATCH (acl:WAFv2WebACL{id: $WAF_ID}), (apigw:APIGatewayStage{id: _APIGW_ID})
    MERGE (acl)-[r:ASSOCIATED_WITH]->(apigw)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UPDATE_TAG
    """

    # reconstruct the APIGW ID from the ARN
    apigw_ids = []
    for arn in apigw_arns:
        base = arn.split(":")[5]
        parts = base.split("/")[-3:]
        apigw_ids.append(f"arn:aws:apigateway:::{parts[0]}/{parts[2]}")

    neo4j_session.run(
        ingest_resources,
        WAF_ID=acl_id,
        APIGW_IDS=apigw_ids,
        UPDATE_TAG=update_tag,
    )


@timeit
def load_waf_acl_rules(neo4j_session, rules, acl_id, update_tag):
    ingest_rules = """
    UNWIND $RULES AS _RULE
    MERGE (rule:WAFv2APIRule{name: _RULE.Name})
    ON CREATE SET rule.firstseen = timestamp()
    SET rule.lastupdated = $UPDATE_TAG, rule.priority = _RULE.Priority
    WITH rule, _RULE
    MATCH (acl:WAFv2WebACL{id: $ACL_ID})
    MERGE (acl)-[e:ENFORCE]->(rule)
    ON CREATE SET e.firstseen = timestamp()
    SET e.lastupdated = $UPDATE_TAG
    WITH rule, _RULE
    UNWIND _RULE.Statement as _STATEMENT
    WITH rule, _STATEMENT
    UNWIND keys(_STATEMENT) as _STATEMENT_TYPE
    WITH rule, _STATEMENT, _STATEMENT_TYPE,
        CASE
            WHEN _STATEMENT_TYPE = 'ManagedRuleGroupStatement'
                THEN _STATEMENT[_STATEMENT_TYPE].VendorName
            ELSE null
        END as _VENDOR_NAME
    SET rule.statementtype = _STATEMENT_TYPE, rule.vendorname = _VENDOR_NAME
    """
    neo4j_session.run(
        ingest_rules,
        RULES=rules,
        UPDATE_TAG=update_tag,
        ACL_ID=acl_id,
    )


@timeit
def load_waf_acl(
        neo4j_session: neo4j.Session, data: List[Dict], current_aws_account_id: str, update_tag: int,
) -> None:
    ingest_acl = """
    MERGE (acl:WAFv2WebACL{id: $ACL_ID})
    ON CREATE SET acl.firstseen = timestamp()
    SET acl.lastupdated = $UPDATE_TAG,
        acl.name = $NAME,
        acl.description = $DESCRIPTION,
        acl.capacity = $CAPACITY,
        acl.managedbyfirewallmanager = $MANAGED_BY_FIREWALL_MANAGER
    WITH acl
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(acl)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UPDATE_TAG
    """
    for acl in data:
        neo4j_session.run(
            ingest_acl,
            ACL_ID=acl['Id'],
            NAME=acl['Name'],
            DESCRIPTION=acl['Description'],
            AWS_ACCOUNT_ID=current_aws_account_id,
            UPDATE_TAG=update_tag,
            CAPACITY=acl['Capacity'],
            MANAGED_BY_FIREWALL_MANAGER=acl['ManagedByFirewallManager'],
        )

        load_waf_acl_rules(neo4j_session, acl['Rules'], acl['Id'], update_tag)

        load_waf_acl_alb_resources(neo4j_session, acl['Resources']["ALBs"], acl["Id"], current_aws_account_id,
                                   update_tag)

        load_waf_acl_apigw_resources(neo4j_session, acl['Resources']["APIGWs"], acl["Id"], update_tag)


@timeit
def cleanup_waf_acl(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    """Delete WAFv2's and dependent resources in the DB without the most recent lastupdated tag."""
    run_cleanup_job('aws_ingest_waf_v2_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_wafv2_acls(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session,
        current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    logger.info("Syncing WAFv2 WebACLs in account '%s'.", current_aws_account_id)
    data = get_waf_acls(boto3_session)
    load_waf_acl(neo4j_session, data, current_aws_account_id, update_tag)

    cleanup_waf_acl(neo4j_session, common_job_parameters)


@timeit
def sync_wafv2(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
        current_aws_account_id: str,
        update_tag: int, common_job_parameters: Dict,
) -> None:
    sync_wafv2_acls(neo4j_session, boto3_session, current_aws_account_id, update_tag, common_job_parameters)
