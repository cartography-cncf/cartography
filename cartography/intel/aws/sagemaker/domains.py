import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.sagemaker.util import sagemaker_handle_regions
from cartography.intel.aws.sagemaker.util import sync_sagemaker_resource
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.sagemaker.domain import AWSSageMakerDomainSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@sagemaker_handle_regions
def get_domains(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get all SageMaker Domains in the given region.
    """
    client = create_boto3_client(boto3_session, "sagemaker", region_name=region)
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
    skip_regions: set[str],
) -> set[str]:
    """
    Sync SageMaker Domains for all specified regions.
    """
    return sync_sagemaker_resource(
        neo4j_session=neo4j_session,
        boto3_session=boto3_session,
        regions=regions,
        current_aws_account_id=current_aws_account_id,
        aws_update_tag=aws_update_tag,
        common_job_parameters=common_job_parameters,
        skip_regions=skip_regions,
        submodule_name="domains",
        get_resources=get_domains,
        transform_resources=transform_domains,
        load_resources=load_domains,
        cleanup_resources=cleanup_domains,
    )
