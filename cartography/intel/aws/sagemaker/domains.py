import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.sagemaker.domain import AWSSageMakerDomainSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_domains(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get all SageMaker Domains in the given region.
    """
    client = boto3_session.client("sagemaker", region_name=region)
    paginator = client.get_paginator("list_domains")
    domains: list[dict[str, Any]] = []

    # Get all domain IDs
    domain_ids: list[str] = []
    for page in paginator.paginate():
        for domain in page.get("Domains", []):
            domain_ids.append(domain["DomainId"])

    # Get detailed information for each domain
    for domain_id in domain_ids:
        response = client.describe_domain(DomainId=domain_id)
        domains.append(response)

    return domains


def transform_domains(
    domains: list[dict[str, Any]],
    region: str,
) -> list[dict[str, Any]]:
    """
    Transform domain data for loading into Neo4j.
    """
    transformed_domains = []

    for domain in domains:
        transformed_domain = {
            "DomainArn": domain.get("DomainArn"),
            "DomainId": domain.get("DomainId"),
            "DomainName": domain.get("DomainName"),
            "Status": domain.get("Status"),
            "CreationTime": domain.get("CreationTime"),
            "LastModifiedTime": domain.get("LastModifiedTime"),
            "Url": domain.get("Url"),
            "HomeEfsFileSystemId": domain.get("HomeEfsFileSystemId"),
            "AuthMode": domain.get("AuthMode"),
            "Region": region,
        }
        transformed_domains.append(transformed_domain)

    return transformed_domains


@timeit
def load_domains(
    neo4j_session: neo4j.Session,
    domains: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load domains into Neo4j.
    """
    load(
        neo4j_session,
        AWSSageMakerDomainSchema(),
        domains,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup_domains(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove domains that no longer exist in AWS.
    """
    GraphJob.from_node_schema(
        AWSSageMakerDomainSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_domains(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync SageMaker Domains for all specified regions.
    """
    for region in regions:
        logger.info(
            "Syncing SageMaker Domains for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        # Get domains from AWS
        domains = get_domains(boto3_session, region)

        # Transform the data
        transformed_domains = transform_domains(domains, region)

        # Load into Neo4j
        load_domains(
            neo4j_session,
            transformed_domains,
            region,
            current_aws_account_id,
            aws_update_tag,
        )

    # Cleanup old domains
    cleanup_domains(neo4j_session, common_job_parameters)
