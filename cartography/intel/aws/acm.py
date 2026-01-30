import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.acm.certificate import ACMCertificateSchema
from cartography.stats import get_stats_client
from cartography.util import aws_handle_regions
from cartography.util import merge_module_sync_metadata
from cartography.util import timeit

logger = logging.getLogger(__name__)
stat_handler = get_stats_client(__name__)


@timeit
@aws_handle_regions
def get_acm_certificates(
    boto3_session: boto3.session.Session, region: str
) -> list[dict[str, Any]]:
    client = boto3_session.client("acm", region_name=region)
    paginator = client.get_paginator("list_certificates")
    summaries: list[dict[str, Any]] = []
    for page in paginator.paginate():
        summaries.extend(page.get("CertificateSummaryList", []))

    details: list[dict[str, Any]] = []
    for summary in summaries:
        arn = summary["CertificateArn"]
        resp = client.describe_certificate(CertificateArn=arn)
        details.append(resp["Certificate"])
    return details


def transform_acm_certificates(
    certificates: list[dict[str, Any]], region: str
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for cert in certificates:
        item: dict[str, Any] = {
            "Arn": cert["CertificateArn"],
            "DomainName": cert.get("DomainName"),
            "Type": cert.get("Type"),
            "Status": cert.get("Status"),
            "KeyAlgorithm": cert.get("KeyAlgorithm"),
            "SignatureAlgorithm": cert.get("SignatureAlgorithm"),
            "NotBefore": cert.get("NotBefore"),
            "NotAfter": cert.get("NotAfter"),
            "InUseBy": cert.get("InUseBy", []),
            "Region": region,
        }
        # Extract ELBV2 Listener ARNs for relationship creation
        listener_arns = [a for a in item["InUseBy"] if ":listener/" in a]
        if listener_arns:
            item["ELBV2ListenerArns"] = listener_arns
        transformed.append(item)
    return transformed


@timeit
def load_acm_certificates(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(data)} ACM certificates for region {region} into graph.")
    load(
        neo4j_session,
        ACMCertificateSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup_acm_certificates(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    logger.debug("Running ACM certificate cleanup job.")
    GraphJob.from_node_schema(ACMCertificateSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            f"Syncing ACM certificates for region {region} in account {current_aws_account_id}."
        )
        certs = get_acm_certificates(boto3_session, region)
        transformed = transform_acm_certificates(certs, region)
        load_acm_certificates(
            neo4j_session,
            transformed,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup_acm_certificates(neo4j_session, common_job_parameters)

    merge_module_sync_metadata(
        neo4j_session,
        group_type="AWSAccount",
        group_id=current_aws_account_id,
        synced_type="ACMCertificate",
        update_tag=update_tag,
        stat_handler=stat_handler,
    )
