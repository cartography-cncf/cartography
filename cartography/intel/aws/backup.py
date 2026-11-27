import logging
from functools import wraps
from typing import Any
from typing import cast

import boto3
import neo4j
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import ReadTimeoutError
from botocore.exceptions import SSLError
from botocore.parsers import ResponseParserError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.backup.plan import AWSBackupBackupPlanSchema
from cartography.models.aws.backup.vault import AWSBackupBackupVaultSchema
from cartography.util import aws_handle_regions
from cartography.util import AWSGetFunc
from cartography.util import timeit

logger = logging.getLogger(__name__)


class BackupTransientRegionFailure(Exception):
    pass


def _raise_on_transient_failure(func: AWSGetFunc) -> AWSGetFunc:
    # aws_handle_regions turns some 5xx and timeouts into [], which cleanup
    # can't tell apart from an empty region.
    @wraps(func)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except ClientError as error:
            status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if (status or 0) >= 500:
                raise BackupTransientRegionFailure(func.__name__) from error
            raise
        except (
            ConnectTimeoutError,
            ReadTimeoutError,
            ResponseParserError,
            SSLError,
        ) as error:
            raise BackupTransientRegionFailure(func.__name__) from error

    return cast(AWSGetFunc, wrapped)


@timeit
@aws_handle_regions
@_raise_on_transient_failure
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
@_raise_on_transient_failure
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
    cleanup_safe = True
    for region in regions:
        logger.info(
            "Syncing Backup for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        try:
            vaults = get_backup_vaults(boto3_session, region)
            plans = get_backup_plans(boto3_session, region)
        except BackupTransientRegionFailure as error:
            cleanup_safe = False
            logger.warning(
                "Skipping Backup for account %s in region %s: %s",
                current_aws_account_id,
                region,
                error,
            )
            continue
        load_backup_vaults(
            neo4j_session,
            vaults,
            region,
            current_aws_account_id,
            update_tag,
        )
        load_backup_plans(
            neo4j_session,
            plans,
            region,
            current_aws_account_id,
            update_tag,
        )
    if cleanup_safe:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping Backup cleanup for account %s to keep last-known-good data.",
            current_aws_account_id,
        )
