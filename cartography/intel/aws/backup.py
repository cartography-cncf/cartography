import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.backup import AWSBackupPlanSchema
from cartography.models.aws.backup import AWSBackupVaultSchema
from cartography.util import aws_handle_regions
from cartography.util import dict_date_to_epoch
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_backup_vaults(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client("backup", region_name=region)
    vaults = []
    paginator = client.get_paginator("list_backup_vaults")
    for page in paginator.paginate():
        vaults.extend(page["BackupVaultList"])
    return vaults


@timeit
@aws_handle_regions
def get_backup_plans(boto3_session: boto3.Session, region: str) -> List[Dict[str, Any]]:
    client = boto3_session.client("backup", region_name=region)
    plans = []
    paginator = client.get_paginator("list_backup_plans")
    for page in paginator.paginate():
        plans.extend(page["BackupPlansList"])
    return plans


def transform_backup_vaults(vaults: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for vault in vaults:
        vault["CreationDate"] = dict_date_to_epoch(vault, "CreationDate")
        vault["LockDate"] = dict_date_to_epoch(vault, "LockDate")
    return vaults


def transform_backup_plans(plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for plan in plans:
        plan["CreationDate"] = dict_date_to_epoch(plan, "CreationDate")
        plan["DeletionDate"] = dict_date_to_epoch(plan, "DeletionDate")
        plan["LastExecutionDate"] = dict_date_to_epoch(plan, "LastExecutionDate")
    return plans


@timeit
def load_backup_vaults(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSBackupVaultSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_backup_plans(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSBackupPlanSchema(),
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
    logger.info("Running AWS Backup cleanup")
    GraphJob.from_node_schema(AWSBackupVaultSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(AWSBackupPlanSchema(), common_job_parameters).run(
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
            f"Syncing AWS Backup for region '{region}' in account '{current_aws_account_id}'."
        )

        vaults = get_backup_vaults(boto3_session, region)
        vaults = transform_backup_vaults(vaults)
        load_backup_vaults(
            neo4j_session, vaults, region, current_aws_account_id, update_tag
        )

        plans = get_backup_plans(boto3_session, region)
        plans = transform_backup_plans(plans)
        load_backup_plans(
            neo4j_session, plans, region, current_aws_account_id, update_tag
        )

    cleanup(neo4j_session, common_job_parameters)
