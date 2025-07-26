import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.auto_scaling_groups import (
    EC2SubnetAutoScalingGroupSchema,
)
from cartography.models.aws.ec2.subnet_instance import EC2SubnetInstanceSchema
from cartography.models.aws.ec2.subnets import EC2SubnetSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_subnet_data(
    boto3_session: boto3.session.Session, region: str
) -> list[dict[str, Any]]:
    client = boto3_session.client(
        "ec2",
        region_name=region,
        config=get_botocore_config(),
    )
    paginator = client.get_paginator("describe_subnets")
    subnets: list[dict[str, Any]] = []
    for page in paginator.paginate():
        subnets.extend(page["Subnets"])
    return subnets


def transform_subnet_data(subnets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Transform subnet data into a loadable format."""
    transformed: list[dict[str, Any]] = []
    for subnet in subnets:
        transformed.append(subnet.copy())
    return transformed


@timeit
def load_subnets(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        EC2SubnetSchema(),
        data,
        Region=region,
        AWS_ID=aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup_subnets(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(EC2SubnetSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(EC2SubnetInstanceSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        EC2SubnetAutoScalingGroupSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_subnets(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing EC2 subnets for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        data = get_subnet_data(boto3_session, region)
        transformed = transform_subnet_data(data)
        load_subnets(
            neo4j_session,
            transformed,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup_subnets(neo4j_session, common_job_parameters)
