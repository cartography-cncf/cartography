import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.internet_gateways import AWSInternetGatewaySchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_internet_gateways(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    client = boto3_session.client(
        "ec2",
        region_name=region,
        config=get_botocore_config(),
    )
    return client.describe_internet_gateways()["InternetGateways"]


def transform_internet_gateways(
    internet_gateways: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
) -> list[dict[str, Any]]:
    """
    Transform internet gateways data, flattening the Attachments list.
    Each attachment becomes a separate entry to handle IGWs attached to multiple VPCs.
    """
    result = []
    for igw in internet_gateways:
        igw_id = igw["InternetGatewayId"]
        owner_id = igw.get("OwnerId", current_aws_account_id)
        # TODO: Right now this won't work in non-AWS commercial (GovCloud, China) as partition is hardcoded
        arn = f"arn:aws:ec2:{region}:{owner_id}:internet-gateway/{igw_id}"

        attachments = igw.get("Attachments", [])
        if attachments:
            # Create one entry per attachment to handle multiple VPCs
            for attachment in attachments:
                result.append(
                    {
                        "InternetGatewayId": igw_id,
                        "OwnerId": owner_id,
                        "Arn": arn,
                        "VpcId": attachment.get("VpcId"),
                    }
                )
        else:
            # IGW without attachments
            result.append(
                {
                    "InternetGatewayId": igw_id,
                    "OwnerId": owner_id,
                    "Arn": arn,
                    "VpcId": None,
                }
            )
    return result


@timeit
def load_internet_gateways(
    neo4j_session: neo4j.Session,
    internet_gateways: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Internet Gateways in %s.", len(internet_gateways), region)
    load(
        neo4j_session,
        AWSInternetGatewaySchema(),
        internet_gateways,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    logger.debug("Running Internet Gateway cleanup job.")
    GraphJob.from_node_schema(
        AWSInternetGatewaySchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_internet_gateways(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing Internet Gateways for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        internet_gateways = get_internet_gateways(boto3_session, region)
        transformed_data = transform_internet_gateways(
            internet_gateways,
            region,
            current_aws_account_id,
        )
        load_internet_gateways(
            neo4j_session,
            transformed_data,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
