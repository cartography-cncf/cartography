import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.cloudfront import AWSCloudFrontDistributionSchema
from cartography.util import aws_handle_regions
from cartography.util import dict_date_to_epoch
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_distributions(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    # CloudFront is global, but we use us-east-1 endpoint typically or just global endpoint.
    # We should only run this if we are in a specific region or if the caller handles it.
    if region != "us-east-1":
        return []

    client = boto3_session.client("cloudfront", region_name="us-east-1")
    distributions = []
    paginator = client.get_paginator("list_distributions")
    for page in paginator.paginate():
        # list_distributions returns 'DistributionList' -> 'Items'
        if "Items" in page.get("DistributionList", {}):
            distributions.extend(page["DistributionList"]["Items"])
    return distributions


def transform_distributions(
    distributions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    for dist in distributions:
        dist["LastModifiedTime"] = dict_date_to_epoch(dist, "LastModifiedTime")
    return distributions


@timeit
def load_distributions(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    # Set region to 'global' for global resources? Or keep it as us-east-1 which is where we fetched it?
    # Usually we use 'us-east-1' or 'global'. let's stick to the passed region (us-east-1).
    load(
        neo4j_session,
        AWSCloudFrontDistributionSchema(),
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
    logger.info("Running AWS CloudFront cleanup")
    GraphJob.from_node_schema(
        AWSCloudFrontDistributionSchema(), common_job_parameters
    ).run(neo4j_session)


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
        # Optimization: Only sync CloudFront in us-east-1
        if region != "us-east-1":
            continue

        logger.info(
            f"Syncing AWS CloudFront for region '{region}' in account '{current_aws_account_id}'."
        )

        distributions = get_distributions(boto3_session, region)
        distributions = transform_distributions(distributions)
        load_distributions(
            neo4j_session, distributions, region, current_aws_account_id, update_tag
        )

    cleanup(neo4j_session, common_job_parameters)
