"""
Intel module for AWS Route 53 registered domains.

Route 53 Domains is a global service; API calls must go to us-east-1.
See: https://docs.aws.amazon.com/Route53/latest/APIReference/API_domains_ListDomains.html
"""

import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.route53.registered_domain import (
    Route53RegisteredDomainSchema,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Route 53 Domains is a global service; API calls must go to us-east-1.
ROUTE53_DOMAINS_REGION = "us-east-1"


@timeit
def get_registered_domains(
    boto3_session: boto3.session.Session,
) -> list[dict[str, Any]]:
    """Fetch registered domains from the Route 53 Domains API."""
    client = create_boto3_client(
        boto3_session,
        "route53domains",
        region_name=ROUTE53_DOMAINS_REGION,
    )
    domains: list[dict[str, Any]] = []
    paginator = client.get_paginator("list_domains")
    for page in paginator.paginate():
        domains.extend(page.get("Domains", []))
    return domains


def transform_registered_domains(
    domains: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for domain in domains:
        domain_name = domain.get("DomainName")
        if not domain_name:
            continue
        transformed.append(
            {
                "id": domain_name,
                "name": domain_name,
                "auto_renew": domain.get("AutoRenew"),
                "transfer_lock": domain.get("TransferLock"),
                "expiry": domain.get("Expiry"),
            },
        )
    return transformed


@timeit
def load_registered_domains(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        Route53RegisteredDomainSchema(),
        data,
        lastupdated=update_tag,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup_registered_domains(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        Route53RegisteredDomainSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync Route 53 registered domains for an account.

    Call after AWSDNSZone nodes are loaded so REGISTERED_DOMAIN edges can match.
    """
    logger.info(
        "Syncing Route53 registered domains for account '%s'.",
        current_aws_account_id,
    )
    raw_domains = get_registered_domains(boto3_session)
    transformed = transform_registered_domains(raw_domains)
    load_registered_domains(
        neo4j_session,
        transformed,
        current_aws_account_id,
        update_tag,
    )
    cleanup_registered_domains(neo4j_session, common_job_parameters)
