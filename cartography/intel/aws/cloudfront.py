"""
Intel module for AWS CloudFront distributions.

CloudFront is AWS's global content delivery network (CDN) service.
CloudFront is a global service, so we only need to query it once from us-east-1.

See: https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_ListDistributions.html
See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudfront/client/list_distributions.html
"""

import logging
import re
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.cloudfront.distribution import CloudFrontDistributionSchema
from cartography.stats import get_stats_client
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)

# CloudFront is a global service, API calls should go to us-east-1
CLOUDFRONT_REGION = "us-east-1"

# Regex pattern to extract S3 bucket name from S3 origin domain names
# Matches patterns like: mybucket.s3.amazonaws.com, mybucket.s3.us-east-1.amazonaws.com,
# mybucket.s3-website-us-east-1.amazonaws.com
S3_BUCKET_PATTERN = re.compile(
    r"^([a-z0-9][a-z0-9.-]*[a-z0-9])\.s3(?:-website)?(?:[.-][a-z0-9-]+)?\.amazonaws\.com$",
)


@timeit
def get_cloudfront_distributions(
    boto3_session: boto3.session.Session,
) -> list[dict[str, Any]]:
    """
    Retrieve all CloudFront distributions.

    CloudFront is a global service, so we query from us-east-1.
    """
    logger.info("Fetching CloudFront distributions")
    client = boto3_session.client("cloudfront", region_name=CLOUDFRONT_REGION)

    distributions: list[dict[str, Any]] = []
    paginator = client.get_paginator("list_distributions")

    for page in paginator.paginate():
        distribution_list = page.get("DistributionList", {})
        items = distribution_list.get("Items", [])
        distributions.extend(items)

    logger.info("Found %d CloudFront distributions", len(distributions))
    return distributions


def _extract_s3_bucket_name(domain_name: str) -> str | None:
    """
    Extract S3 bucket name from an S3 origin domain name.

    Examples:
        mybucket.s3.amazonaws.com -> mybucket
        mybucket.s3.us-east-1.amazonaws.com -> mybucket
        mybucket.s3-website-us-east-1.amazonaws.com -> mybucket

    Returns None if the domain is not an S3 bucket domain.
    """
    match = S3_BUCKET_PATTERN.match(domain_name.lower())
    if match:
        return match.group(1)
    return None


def _extract_lambda_arns_from_cache_behavior(
    cache_behavior: dict[str, Any],
) -> list[str]:
    """
    Extract Lambda function ARNs from a cache behavior's LambdaFunctionAssociations.
    """
    arns: list[str] = []
    lambda_associations = cache_behavior.get("LambdaFunctionAssociations", {})
    items = lambda_associations.get("Items", [])
    for item in items:
        arn = item.get("LambdaFunctionARN")
        if arn:
            arns.append(arn)
    return arns


def transform_cloudfront_distributions(
    distributions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Transform CloudFront distribution data for ingestion into the graph.

    Extracts:
    - Aliases from the Aliases structure
    - S3 bucket names from origin domain names for relationship creation
    - Lambda function ARNs from cache behavior associations
    - ViewerCertificate configuration
    - GeoRestriction configuration
    - DefaultCacheBehavior viewer protocol policy
    """
    transformed: list[dict[str, Any]] = []

    for dist in distributions:
        item: dict[str, Any] = {
            # Core identifiers
            "Id": dist["Id"],
            "ARN": dist["ARN"],
            "ETag": dist.get("ETag"),
            # Domain and naming
            "DomainName": dist["DomainName"],
            "Comment": dist.get("Comment"),
            # Status and configuration
            "Status": dist["Status"],
            "Enabled": dist["Enabled"],
            "PriceClass": dist.get("PriceClass"),
            "HttpVersion": dist.get("HttpVersion"),
            "IsIPV6Enabled": dist.get("IsIPV6Enabled"),
            "Staging": dist.get("Staging"),
            "LastModifiedTime": dist.get("LastModifiedTime"),
            "WebACLId": dist.get("WebACLId"),
        }

        # Extract aliases
        aliases_struct = dist.get("Aliases", {})
        aliases_items = aliases_struct.get("Items", [])
        item["Aliases"] = aliases_items if aliases_items else None

        # Extract viewer protocol policy from default cache behavior
        default_cache_behavior = dist.get("DefaultCacheBehavior", {})
        item["ViewerProtocolPolicy"] = default_cache_behavior.get(
            "ViewerProtocolPolicy",
        )

        # Extract ViewerCertificate configuration
        viewer_cert = dist.get("ViewerCertificate", {})
        item["ACMCertificateArn"] = viewer_cert.get("ACMCertificateArn")
        item["CloudFrontDefaultCertificate"] = viewer_cert.get(
            "CloudFrontDefaultCertificate",
        )
        item["MinimumProtocolVersion"] = viewer_cert.get("MinimumProtocolVersion")
        item["SSLSupportMethod"] = viewer_cert.get("SSLSupportMethod")
        item["IAMCertificateId"] = viewer_cert.get("IAMCertificateId")

        # Extract GeoRestriction configuration
        restrictions = dist.get("Restrictions", {})
        geo_restriction = restrictions.get("GeoRestriction", {})
        item["GeoRestrictionType"] = geo_restriction.get("RestrictionType")
        geo_locations = geo_restriction.get("Items", [])
        item["GeoRestrictionLocations"] = geo_locations if geo_locations else None

        # Extract S3 bucket names from origins for relationship creation
        s3_bucket_names: list[str] = []
        origins = dist.get("Origins", {})
        origin_items = origins.get("Items", [])
        for origin in origin_items:
            domain_name = origin.get("DomainName", "")
            bucket_name = _extract_s3_bucket_name(domain_name)
            if bucket_name and bucket_name not in s3_bucket_names:
                s3_bucket_names.append(bucket_name)

        if s3_bucket_names:
            item["s3_origin_bucket_names"] = s3_bucket_names

        # Extract Lambda function ARNs from cache behaviors
        lambda_arns: list[str] = []

        # From default cache behavior
        lambda_arns.extend(
            _extract_lambda_arns_from_cache_behavior(default_cache_behavior)
        )

        # From additional cache behaviors
        cache_behaviors = dist.get("CacheBehaviors", {})
        cache_behavior_items = cache_behaviors.get("Items", [])
        for cache_behavior in cache_behavior_items:
            lambda_arns.extend(_extract_lambda_arns_from_cache_behavior(cache_behavior))

        # Deduplicate Lambda ARNs
        if lambda_arns:
            item["lambda_function_arns"] = list(set(lambda_arns))

        transformed.append(item)

    return transformed


@timeit
def load_cloudfront_distributions(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load CloudFront distributions into the graph database.
    """
    logger.info("Loading %d CloudFront distributions into graph", len(data))

    load(
        neo4j_session,
        CloudFrontDistributionSchema(),
        data,
        lastupdated=update_tag,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup_cloudfront_distributions(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove stale CloudFront distribution nodes from the graph.
    """
    logger.debug("Running CloudFront distribution cleanup job")

    GraphJob.from_node_schema(
        CloudFrontDistributionSchema(),
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
    """
    Sync AWS CloudFront distributions.

    Note: CloudFront is a global service, so we only query once regardless of
    the regions parameter. The regions parameter is accepted for interface
    consistency with other AWS modules but is not used.
    """
    logger.info(
        "Syncing CloudFront distributions for account %s",
        current_aws_account_id,
    )

    # Fetch distributions (global service, only need to call once)
    distributions = get_cloudfront_distributions(boto3_session)

    if not distributions:
        logger.info("No CloudFront distributions found")
    else:
        # Transform data for ingestion
        transformed = transform_cloudfront_distributions(distributions)

        # Load into Neo4j
        load_cloudfront_distributions(
            neo4j_session,
            transformed,
            current_aws_account_id,
            update_tag,
        )

    # Clean up stale nodes
    cleanup_cloudfront_distributions(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="CloudFrontDistribution",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )

    logger.info("Completed CloudFront sync for account %s", current_aws_account_id)
