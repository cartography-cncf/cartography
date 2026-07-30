import logging
import time
from typing import Any

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.service_regions import (
    filter_regions_to_supported_service_regions,
)
from cartography.models.aws.apprunner import AppRunnerServiceSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

# App Runner DescribeService default quota is 10 req/s. Sleep briefly between
# describes so a large account does not burn the quota and restart pagination
# from scratch via aws_handle_regions retries.
DESCRIBE_SLEEP = 0.1


@timeit
@aws_handle_regions
def get_apprunner_services(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    client = create_boto3_client(boto3_session, "apprunner", region_name=region)
    paginator = client.get_paginator("list_services")
    services: list[dict[str, Any]] = []
    for page in paginator.paginate():
        services.extend(page.get("ServiceSummaryList", []))

    described_services: list[dict[str, Any]] = []
    for service in services:
        service_arn = service["ServiceArn"]
        try:
            desc_response = client.describe_service(ServiceArn=service_arn)
        except botocore.exceptions.ClientError as e:
            # Service deleted between list and describe — skip, do not fail the sync.
            if e.response.get("Error", {}).get("Code") == "ResourceNotFoundException":
                logger.warning(
                    "App Runner service %s not found during describe; skipping.",
                    service_arn,
                )
                continue
            raise
        described_services.append(desc_response["Service"])
        time.sleep(DESCRIBE_SLEEP)
    return described_services


def transform_apprunner_services(
    services: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Flatten nested App Runner configuration fields for Neo4j ingestion.
    """
    transformed: list[dict[str, Any]] = []
    for svc in services:
        svc = dict(svc)

        source_config = svc.get("SourceConfiguration", {}) or {}
        image_repo = source_config.get("ImageRepository", {}) or {}
        code_repo = source_config.get("CodeRepository", {}) or {}
        svc["ImageIdentifier"] = image_repo.get("ImageIdentifier")
        svc["CodeRepositoryUrl"] = code_repo.get("RepositoryUrl")
        svc["AutoDeploymentsEnabled"] = source_config.get("AutoDeploymentsEnabled")
        auth_config = source_config.get("AuthenticationConfiguration", {}) or {}
        svc["AccessRoleArn"] = auth_config.get("AccessRoleArn")

        instance_config = svc.get("InstanceConfiguration", {}) or {}
        svc["Cpu"] = instance_config.get("Cpu")
        svc["Memory"] = instance_config.get("Memory")
        svc["InstanceRoleArn"] = instance_config.get("InstanceRoleArn")

        network_config = svc.get("NetworkConfiguration", {}) or {}
        egress_config = network_config.get("EgressConfiguration", {}) or {}
        svc["EgressType"] = egress_config.get("EgressType")
        ingress_config = network_config.get("IngressConfiguration", {}) or {}
        svc["IsPubliclyAccessible"] = ingress_config.get("IsPubliclyAccessible")

        transformed.append(svc)
    return transformed


@timeit
def load_apprunner_services(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        "Loading AppRunner %s services for region '%s' into graph.",
        len(data),
        region,
    )
    load(
        neo4j_session,
        AppRunnerServiceSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Running AppRunner cleanup job.")
    cleanup_job = GraphJob.from_node_schema(
        AppRunnerServiceSchema(),
        common_job_parameters,
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    apprunner_regions, unsupported_regions = (
        filter_regions_to_supported_service_regions(
            boto3_session,
            "apprunner",
            regions,
        )
    )
    for region in unsupported_regions:
        logger.info(
            "Skipping AppRunner sync for unsupported region '%s'.",
            region,
        )

    for region in apprunner_regions:
        logger.info(
            "Syncing AppRunner for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )

        services = get_apprunner_services(boto3_session, region)
        transformed_services = transform_apprunner_services(services)
        load_apprunner_services(
            neo4j_session,
            transformed_services,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
