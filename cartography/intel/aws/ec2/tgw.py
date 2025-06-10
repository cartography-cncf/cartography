import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.ec2.transit_gateways import TransitGatewayAttachmentSchema
from cartography.models.aws.ec2.transit_gateways import TransitGatewaySchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_transit_gateways(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
    client = boto3_session.client(
        "ec2",
        region_name=region,
        config=get_botocore_config(),
    )
    data: List[Dict] = []
    try:
        data = client.describe_transit_gateways()["TransitGateways"]
    except botocore.exceptions.ClientError as e:
        logger.warning(
            "Could not retrieve Transit Gateways due to boto3 error %s: %s. Skipping.",
            e.response["Error"]["Code"],
            e.response["Error"]["Message"],
        )
    return data


@timeit
@aws_handle_regions
def get_tgw_attachments(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
    client = boto3_session.client(
        "ec2",
        region_name=region,
        config=get_botocore_config(),
    )
    tgw_attachments: List[Dict] = []
    try:
        paginator = client.get_paginator("describe_transit_gateway_attachments")
        for page in paginator.paginate():
            tgw_attachments.extend(page["TransitGatewayAttachments"])
    except botocore.exceptions.ClientError as e:
        logger.warning(
            "Could not retrieve Transit Gateway Attachments due to boto3 error %s: %s. Skipping.",
            e.response["Error"]["Code"],
            e.response["Error"]["Message"],
        )
    return tgw_attachments


@timeit
@aws_handle_regions
def get_tgw_vpc_attachments(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
    client = boto3_session.client(
        "ec2",
        region_name=region,
        config=get_botocore_config(),
    )
    tgw_vpc_attachments: List[Dict] = []
    try:
        paginator = client.get_paginator("describe_transit_gateway_vpc_attachments")
        for page in paginator.paginate():
            tgw_vpc_attachments.extend(page["TransitGatewayVpcAttachments"])
    except botocore.exceptions.ClientError as e:
        logger.warning(
            "Could not retrieve Transit Gateway VPC Attachments due to boto3 error %s: %s. Skipping.",
            e.response["Error"]["Code"],
            e.response["Error"]["Message"],
        )
    return tgw_vpc_attachments


def transform_transit_gateways(
    tgws: List[Dict[str, Any]],
    current_aws_account_id: str,
) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for tgw in tgws:
        record = {
            "TgwId": tgw["TransitGatewayId"],
            "ARN": tgw["TransitGatewayArn"],
            "OwnerId": tgw["OwnerId"],
            "State": tgw["State"],
            "Description": tgw.get("Description"),
            "SharedAccountId": (
                current_aws_account_id
                if tgw["OwnerId"] != current_aws_account_id
                else None
            ),
        }
        result.append(record)
    return result


def transform_tgw_attachments(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    transformed: List[Dict[str, Any]] = []
    for item in data:
        transformed.append(
            {
                "TransitGatewayAttachmentId": item["TransitGatewayAttachmentId"],
                "TransitGatewayId": item["TransitGatewayId"],
                "ResourceType": item.get("ResourceType"),
                "State": item["State"],
                "VpcId": item.get("VpcId"),
                "SubnetIds": item.get("SubnetIds", []),
            }
        )
    return transformed


@timeit
def load_transit_gateways(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        TransitGatewaySchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_tgw_attachments(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        TransitGatewayAttachmentSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup_transit_gateways(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    GraphJob.from_node_schema(TransitGatewaySchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(
        TransitGatewayAttachmentSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync_transit_gateways(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing AWS Transit Gateways for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        tgws = get_transit_gateways(boto3_session, region)
        transformed_tgws = transform_transit_gateways(tgws, current_aws_account_id)
        load_transit_gateways(
            neo4j_session,
            transformed_tgws,
            region,
            current_aws_account_id,
            update_tag,
        )

        logger.debug(
            "Syncing AWS Transit Gateway Attachments for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        attachments = get_tgw_attachments(boto3_session, region)
        vpc_attachments = get_tgw_vpc_attachments(boto3_session, region)
        transformed_attachments = transform_tgw_attachments(
            attachments + vpc_attachments
        )
        load_tgw_attachments(
            neo4j_session,
            transformed_attachments,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup_transit_gateways(neo4j_session, common_job_parameters)
