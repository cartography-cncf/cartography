import logging
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.s3.account_public_access_block import (
    S3AccountPublicAccessBlockSchema,
)
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
@aws_handle_regions
def get_account_public_access_block(
    boto3_session: boto3.session.Session, region: str, account_id: str
) -> List[Dict]:
    """
    Get the S3 Account Public Access Block settings for a region.
    Returns a list containing at most one item (the block configuration).
    """
    client = boto3_session.client("s3control", region_name=region)
    try:
        # Use the provided account_id instead of retrieving it
        response = client.get_public_access_block(AccountId=account_id)
        return [response]
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchPublicAccessBlockConfiguration":
            logger.warning(
                f"No public access block configuration found for account {account_id} in region {region}"
            )
            return []
        else:
            raise


def transform_account_public_access_block(
    public_access_blocks: List[Dict],
    region: str,
    aws_account_id: str,
) -> List[Dict]:
    """
    Transform S3 Account Public Access Block data for ingestion.
    """
    transformed_data = []

    for public_access_block in public_access_blocks:
        pab = public_access_block.get("PublicAccessBlockConfiguration", {})
        transformed = {
            "id": f"{aws_account_id}:{region}",
            "account_id": aws_account_id,
            "region": region,
            "block_public_acls": pab.get("BlockPublicAcls"),
            "ignore_public_acls": pab.get("IgnorePublicAcls"),
            "block_public_policy": pab.get("BlockPublicPolicy"),
            "restrict_public_buckets": pab.get("RestrictPublicBuckets"),
        }
        transformed_data.append(transformed)

    return transformed_data


@timeit
def load_account_public_access_block(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load S3 Account Public Access Block information into the graph.
    """
    logger.info(
        f"Loading {len(data)} S3 Account Public Access Block configurations for region {region} into graph."
    )

    load(
        neo4j_session,
        S3AccountPublicAccessBlockSchema(),
        data,
        lastupdated=update_tag,
        region=region,
        AWS_ID=aws_account_id,
    )


@timeit
def cleanup_account_public_access_block(
    neo4j_session: neo4j.Session, common_job_parameters: Dict
) -> None:
    """
    Run S3 Account Public Access Block cleanup job.
    """
    logger.debug("Running S3 Account Public Access Block cleanup job.")
    cleanup_job = GraphJob.from_node_schema(
        S3AccountPublicAccessBlockSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """
    Sync S3 Account Public Access Block settings for all regions.
    """
    for region in regions:
        logger.info(
            f"Syncing S3 Account Public Access Block for {region} in account {current_aws_account_id}"
        )

        public_access_blocks = get_account_public_access_block(
            boto3_session, region, current_aws_account_id
        )
        transformed_data = transform_account_public_access_block(
            public_access_blocks,
            region,
            current_aws_account_id,
        )

        # Removed the unnecessary if check
        load_account_public_access_block(
            neo4j_session,
            transformed_data,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup_account_public_access_block(neo4j_session, common_job_parameters)

    # Record that we've synced this module
    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="S3AccountPublicAccessBlock",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
