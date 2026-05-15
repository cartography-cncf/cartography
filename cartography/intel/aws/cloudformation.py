import logging
import time
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError
from cloudconsolelink.clouds.aws import AWSLinker

from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
@aws_handle_regions
def get_cloudformation_stack(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    stacks = []
    try:
        client = boto3_session.client('cloudformation', region_name=region, config=get_botocore_config())
        paginator = client.get_paginator('describe_stacks')

        page_iterator = paginator.paginate()
        for page in page_iterator:
            stacks.extend(page['Stacks'])

        return stacks

    except ClientError as e:
        logger.error(f'Failed to call cloudformation describe_stacks: {region} - {e}')
        return stacks


@timeit
def transform_stack(sts: List[Dict], region: str) -> List[Dict]:
    stacks = []
    for stack in sts:
        stack['region'] = region
        stack['arn'] = stack['StackId']
        stack['consolelink'] = aws_console_link.get_console_link(arn=stack['arn'])
        stacks.append(stack)

    return stacks


def load_cloudformation_stack(session: neo4j.Session, stacks: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.execute_write(_load_cloudformation_stack_tx, stacks, current_aws_account_id, aws_update_tag)


@timeit
def _load_cloudformation_stack_tx(tx: neo4j.Transaction, stacks: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    query: str = """
    UNWIND $Records as record
    MERGE (stack:AWSCloudformationStack{id: record.StackId})
    ON CREATE SET stack.firstseen = timestamp(),
        stack.arn = record.StackId
    SET stack.lastupdated = $aws_update_tag,
        stack.name = record.StackName,
        stack.region = record.region,
        stack.change_set_id = record.ChangeSetId,
        stack.description = record.Description,
        stack.consolelink = record.consolelink,
        stack.creation_time = record.CreationTime,
        stack.deletion_time = record.DeletionTime,
        stack.stack_status = record.StackStatus,
        stack.stack_status_reason = record.StackStatusReason,
        stack.disable_rollback = record.DisableRollback,
        stack.role_arn = record.RoleARN,
        stack.enable_termination_protection = record.EnableTerminationProtection,
        stack.root_id = record.RootId,
        stack.parent_id = record.ParentId
    WITH stack
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(stack)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    tx.run(
        query,
        Records=stacks,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_cloudformation_stack(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_cloudformation_stack_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing Cloudformation for account '%s', at %s.", current_aws_account_id, tic)

    stacks = []
    for region in regions:
        logger.info("Syncing Cloudformation for region '%s' in account '%s'.", region, current_aws_account_id)

        sts = get_cloudformation_stack(boto3_session, region)

        stacks.extend(transform_stack(sts, region))

    logger.info(f"Total Cloudformation Stacks: {len(stacks)}")

    load_cloudformation_stack(neo4j_session, stacks, current_aws_account_id, update_tag)

    cleanup_cloudformation_stack(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Cloudformation: {toc - tic:0.4f} seconds")
