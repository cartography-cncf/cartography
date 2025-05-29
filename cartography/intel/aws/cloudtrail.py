import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.cloudtrail.trail import CloudTrailTrailSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_cloudtrail_trails(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "cloudtrail", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("list_trails")
    trails = []
    for page in paginator.paginate():
        trails.extend(page["Trails"])

    # CloudTrail multi-region trails are shown in list_trails,
    # but the get_trail call only works in the home region
    trails_filtered = [trail for trail in trails if trail.get("HomeRegion") == region]
    return trails_filtered


@timeit
def get_cloudtrail_trail(
    boto3_session: boto3.Session,
    region: str,
    trail_name: str,
) -> Dict[str, Any]:

    client = boto3_session.client(
        "cloudtrail", region_name=region, config=get_botocore_config()
    )
    trail_details: Dict[str, Any] = {}
    try:
        response = client.get_trail(Name=trail_name)
        trail_details = response["Trail"]
    except botocore.exceptions.ClientError as e:
        code = e.response["Error"]["Code"]
        msg = e.response["Error"]["Message"]
        logger.warning(
            f"Could not run CloudTrail get_trail due to boto3 error {code}: {msg}. Skipping.",
        )
    return trail_details


@timeit
def load_cloudtrail_trails(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading CloudTrail {len(data)} trails for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        CloudTrailTrailSchema(),
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
    logger.debug("Running CloudTrail cleanup job.")
    cleanup_job = GraphJob.from_node_schema(
        CloudTrailTrailSchema(), common_job_parameters
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
            f"Syncing CloudTrail for region '{region}' in account '{current_aws_account_id}'.",
        )
        trails = get_cloudtrail_trails(boto3_session, region)
        trail_data: List[Dict[str, Any]] = []
        for trail in trails:
            trail_name = trail["Name"]
            trail_details = get_cloudtrail_trail(
                boto3_session,
                region,
                trail_name,
            )
            if trail_details:
                trail_data.append(trail_details)

        load_cloudtrail_trails(
            neo4j_session,
            trail_data,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
