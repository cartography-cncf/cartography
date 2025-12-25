import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2 import AWSEc2VpcEndpointServiceSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_vpc_endpoint_services(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client("ec2", region_name=region)
    services = []
    # describe_vpc_endpoint_service_configurations lists services created by the account
    paginator = client.get_paginator("describe_vpc_endpoint_service_configurations")
    for page in paginator.paginate():
        services.extend(page["ServiceConfigurations"])
    return services


def transform_vpc_endpoint_services(
    services: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    return services


@timeit
def load_vpc_endpoint_services(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSEc2VpcEndpointServiceSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup_vpc_endpoint_services(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        AWSEc2VpcEndpointServiceSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync_vpc_endpoint_services(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            f"Syncing AWS VPC Endpoint Services for region '{region}' in account '{current_aws_account_id}'."
        )

        services = get_vpc_endpoint_services(boto3_session, region)
        services = transform_vpc_endpoint_services(services)
        load_vpc_endpoint_services(
            neo4j_session, services, region, current_aws_account_id, update_tag
        )

    cleanup_vpc_endpoint_services(neo4j_session, common_job_parameters)
