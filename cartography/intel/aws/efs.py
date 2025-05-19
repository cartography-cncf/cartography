import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.efs.mount_target import EfsMountTargetSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_efs_mount_targets(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "efs", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("describe_mount_targets")
    mountTargets = []
    for page in paginator.paginate():
        mountTargets.extend(page["MountTargets"])
    return mountTargets


@timeit
def load_efs_mount_targets(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading Efs {len(data)} mount targets for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        EfsMountTargetSchema(),
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
    logger.debug("Running Efs cleanup job.")
    cleanup_job = GraphJob.from_node_schema(
        EfsMountTargetSchema(), common_job_parameters
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
            f"Syncing Efs for region '{region}' in account '{current_aws_account_id}'.",
        )
        mountTargets = get_efs_mount_targets(boto3_session, region)
        mount_target_data: List[Dict[str, Any]] = []
        for mountTarget in mountTargets:
            mount_target_data.append(mountTarget)

        load_efs_mount_targets(
            neo4j_session,
            mount_target_data,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
