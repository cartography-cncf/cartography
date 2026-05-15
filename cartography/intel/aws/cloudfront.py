import logging
import time
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError
from cloudconsolelink.clouds.aws import AWSLinker

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


@timeit
@aws_handle_regions
def get_cloudfront_distributions(boto3_session: boto3.session.Session) -> List[Dict]:
    distributions = []
    try:
        client = boto3_session.client('cloudfront')
        paginator = client.get_paginator('list_distributions')

        page_iterator = paginator.paginate()
        for page in page_iterator:
            distributions.extend(page.get('DistributionList', {}).get('Items', []))

        return distributions

    except ClientError as e:
        logger.error(f'Failed to call CloudFront list_distributions: {e}')
        return distributions


@timeit
def transform_distribution(dists: List[Dict]) -> List[Dict]:
    distributions = []
    for distribution in dists:
        bucket_items = distribution.get("Origins", {}).get("Items", [])
        bucket_names = []
        for item in bucket_items:
            bucket_id = item.get("Id", "")

            if bucket_id.startswith("S3-"):
                bucket_name = bucket_id[3:]
                bucket_names.append(bucket_name)

        distribution['s3BucketNames'] = bucket_names
        distribution['region'] = 'global'
        distribution['arn'] = distribution['ARN']
        distribution['consolelink'] = aws_console_link.get_console_link(arn=distribution['arn'])
        distributions.append(distribution)

    return distributions


def load_cloudfront_distributions(session: neo4j.Session, distributions: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    session.execute_write(_load_cloudfront_distributions_tx, distributions, current_aws_account_id, aws_update_tag)


@timeit
def _load_cloudfront_distributions_tx(tx: neo4j.Transaction, distributions: List[Dict], current_aws_account_id: str, aws_update_tag: int) -> None:
    query: str = """
    UNWIND $Records as record
    MERGE (distribution:AWSCloudfrontDistribution{id: record.ARN})
    ON CREATE SET distribution.firstseen = timestamp(),
        distribution.arn = record.ARN
    SET distribution.lastupdated = $aws_update_tag,
        distribution.name = record.Id,
        distribution.region = record.region,
        distribution.status = record.Status,
        distribution.consolelink = record.consolelink,
        distribution.domain_name = record.DomainName,
        distribution.comment = record.Comment,
        distribution.price_class = record.PriceClass,
        distribution.enabled = record.Enabled,
        distribution.viewer_protocol_policy = record.DefaultCacheBehavior.ViewerProtocolPolicy,
        distribution.web_acl_id = record.WebACLId,
        distribution.is_ipv6_enabled = record.IsIPV6Enabled,
        distribution.http_version = record.HttpVersion,
        distribution.s3_bucket_names = record.s3BucketNames
    WITH distribution, record
    MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (owner)-[r:RESOURCE]->(distribution)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    WITH distribution, record
    UNWIND record.s3BucketNames AS bucket_name
    MATCH (bucket:S3Bucket {name: bucket_name})
    MERGE (distribution)-[rel:LINKED_TO]->(bucket)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $aws_update_tag
    """

    tx.run(
        query,
        Records=distributions,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_cloudfront_distributions(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_cloudfront_distributions_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing Cloudfront for account '%s', at %s.", current_aws_account_id, tic)

    dists = get_cloudfront_distributions(boto3_session)
    distributions = transform_distribution(dists)

    logger.info(f"Total Cloudfront Distributions: {len(distributions)}")

    load_cloudfront_distributions(neo4j_session, distributions, current_aws_account_id, update_tag)

    cleanup_cloudfront_distributions(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process Cloudfront: {toc - tic:0.4f} seconds")
