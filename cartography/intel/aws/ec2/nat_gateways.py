import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.nat_gateways import AWSNatGatewaySchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


def _get_aws_partition(region: str) -> str:
    if region.startswith("us-gov-"):
        return "aws-us-gov"
    if region.startswith("cn-"):
        return "aws-cn"
    return "aws"


@timeit
@aws_handle_regions
def get_nat_gateways(
    boto3_session: boto3.session.Session, region: str
) -> list[dict[str, Any]]:
    client = boto3_session.client(
        "ec2", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("describe_nat_gateways")
    nat_gateways: list[dict[str, Any]] = []
    for page in paginator.paginate():
        nat_gateways.extend(page["NatGateways"])
    return nat_gateways


def transform_nat_gateways(
    nat_gateways: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    partition: str = "aws",
) -> list[dict[str, Any]]:
    """
    Transform NAT gateway data, flattening the primary NatGatewayAddresses entry.
    """
    result = []
    for ngw in nat_gateways:
        ngw_id = ngw["NatGatewayId"]
        arn = (
            f"arn:{partition}:ec2:{region}:{current_aws_account_id}:natgateway/{ngw_id}"
        )

        # Flatten the primary address entry; prefer the entry marked IsPrimary
        addresses = ngw.get("NatGatewayAddresses", [])
        primary = next(
            (addr for addr in addresses if addr.get("IsPrimary", False)),
            addresses[0] if addresses else {},
        )

        create_time = ngw.get("CreateTime")
        result.append(
            {
                "NatGatewayId": ngw_id,
                "SubnetId": ngw.get("SubnetId"),
                "VpcId": ngw.get("VpcId"),
                "State": ngw.get("State"),
                "CreateTime": str(create_time) if create_time else None,
                "AllocationId": primary.get("AllocationId"),
                "NetworkInterfaceId": primary.get("NetworkInterfaceId"),
                "PrivateIp": primary.get("PrivateIp"),
                "PublicIp": primary.get("PublicIp"),
                "ConnectivityType": ngw.get("ConnectivityType"),
                "Arn": arn,
            }
        )
    return result


@timeit
def load_nat_gateways(
    neo4j_session: neo4j.Session,
    nat_gateways: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d NAT Gateways in %s.", len(nat_gateways), region)
    load(
        neo4j_session,
        AWSNatGatewaySchema(),
        nat_gateways,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    logger.debug("Running NAT Gateway cleanup job.")
    GraphJob.from_node_schema(AWSNatGatewaySchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_nat_gateways(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing NAT Gateways for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        nat_gateways = get_nat_gateways(boto3_session, region)
        partition = _get_aws_partition(region)
        transformed_data = transform_nat_gateways(
            nat_gateways, region, current_aws_account_id, partition
        )
        load_nat_gateways(
            neo4j_session, transformed_data, region, current_aws_account_id, update_tag
        )
    cleanup(neo4j_session, common_job_parameters)
