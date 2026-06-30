import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.models.aws.apprunner.service import AppRunnerServiceSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_apprunner_services(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    client = create_boto3_client(
        boto3_session,
        "apprunner",
        region_name=region,
        config=get_botocore_config(),
    )
    paginator = client.get_paginator("list_services")
    services: list[dict[str, Any]] = []
    for page in paginator.paginate():
        for summary in page.get("ServiceSummaryList", []):
            response = client.describe_service(ServiceArn=summary["ServiceArn"])
            services.append(response["Service"])
    return services


def transform_apprunner_services(
    services: list[dict[str, Any]],
    region: str,
) -> list[dict[str, Any]]:
    transformed_services = []
    for service in services:
        transformed_services.append(
            {
                "ServiceArn": service["ServiceArn"],
                "ServiceId": service.get("ServiceId"),
                "ServiceName": service.get("ServiceName"),
                "ServiceUrl": service.get("ServiceUrl"),
                "Status": service.get("Status"),
                "InstanceRoleArn": service.get("InstanceConfiguration", {}).get(
                    "InstanceRoleArn"
                ),
                "Region": region,
            },
        )
    return transformed_services


@timeit
def load_apprunner_services(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        "Loading %d App Runner services for region '%s' into graph.",
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
    logger.debug("Running App Runner cleanup job.")
    GraphJob.from_node_schema(AppRunnerServiceSchema(), common_job_parameters).run(
        neo4j_session,
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
            "Syncing App Runner services for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        raw_services = get_apprunner_services(boto3_session, region)
        transformed_services = transform_apprunner_services(raw_services, region)
        load_apprunner_services(
            neo4j_session,
            transformed_services,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
