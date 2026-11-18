import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.backup.plan import AWSBackupBackupPlanSchema
from cartography.models.aws.backup.vault import AWSBackupBackupVaultSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_backup_vaults(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    client = create_boto3_client(
        boto3_session,
        "backup",
        region_name=region,
    )
    paginator = client.get_paginator("list_backup_vaults")
    vaults: list[dict[str, Any]] = []
    for page in paginator.paginate():
        vaults.extend(page.get("BackupVaultList", []))
    return vaults


@timeit
@aws_handle_regions
def get_backup_plans(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    client = create_boto3_client(
        boto3_session,
        "backup",
        region_name=region,
    )
    paginator = client.get_paginator("list_backup_plans")
    plans: list[dict[str, Any]] = []
    for page in paginator.paginate():
        plans.extend(page.get("BackupPlansList", []))
    return plans


@timeit
def load_backup_vaults(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        "Loading %d Backup vaults for region '%s' into graph.",
        len(data),
        region,
    )
    load(
        neo4j_session,
        AWSBackupBackupVaultSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_backup_plans(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        "Loading %d Backup plans for region '%s' into graph.",
        len(data),
        region,
    )
    load(
        neo4j_session,
        AWSBackupBackupPlanSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Running Backup cleanup job.")
    GraphJob.from_node_schema(
        AWSBackupBackupVaultSchema(),
        common_job_parameters,
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        AWSBackupBackupPlanSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing Backup for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        vaults = get_backup_vaults(boto3_session, region)
        load_backup_vaults(
            neo4j_session,
            vaults,
            region,
            current_aws_account_id,
            update_tag,
        )
        plans = get_backup_plans(boto3_session, region)
        load_backup_plans(
            neo4j_session,
            plans,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
