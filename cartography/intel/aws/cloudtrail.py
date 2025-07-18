import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
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

    trails = client.describe_trails()["trailList"]
    trails_filtered = [trail for trail in trails if trail.get("HomeRegion") == region]

    return trails_filtered


def transform_cloudtrail_trails(
    trails: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    """
    Transform CloudTrail trail data for ingestion
    """
    for trail in trails:
        arn = trail.get("CloudWatchLogsLogGroupArn")
        if arn:
            trail["CloudWatchLogsLogGroupArn"] = arn.split(":*")[0]

    return trails


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
        trails_filtered = get_cloudtrail_trails(boto3_session, region)
        trails = transform_cloudtrail_trails(trails_filtered, region)

        load_cloudtrail_trails(
            neo4j_session,
            trails,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
