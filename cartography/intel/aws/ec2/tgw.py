import logging
from typing import Any

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.models.aws.ec2.tgw import AWSTransitGatewayAttachmentSchema
from cartography.models.aws.ec2.tgw import AWSTransitGatewaySchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_transit_gateways(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict]:
    client = create_boto3_client(
        boto3_session,
        "ec2",
        region_name=region,
        config=get_botocore_config(),
    )
    data: list[dict] = []
    try:
        data = client.describe_transit_gateways()["TransitGateways"]
    except botocore.exceptions.ClientError as e:
        # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/error-handling.html#parsing-error-responses-and-catching-exceptions-from-aws-services
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
) -> list[dict]:
    client = create_boto3_client(
        boto3_session,
        "ec2",
        region_name=region,
        config=get_botocore_config(),
    )
    tgw_attachments: list[dict] = []
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
) -> list[dict]:
    client = create_boto3_client(
        boto3_session,
        "ec2",
        region_name=region,
        config=get_botocore_config(),
    )
    tgw_vpc_attachments: list[dict] = []
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
    data: list[dict],
    current_aws_account_id: str,
) -> list[dict[str, Any]]:
    for tgw in data:
        tgw["Description"] = tgw.get("Description")
        # Set conditional SHARED_WITH field: only for TGWs owned by a different account
        tgw["_shared_with_account_id"] = (
            current_aws_account_id if tgw["OwnerId"] != current_aws_account_id else None
        )
    return data


def transform_tgw_attachments(
    tgw_attachments: list[dict],
    tgw_vpc_attachments: list[dict],
) -> list[dict[str, Any]]:
    # Merge regular and VPC attachment data by attachment ID
    attachments_by_id: dict[str, dict[str, Any]] = {}
    for att in tgw_attachments:
        att_id = att["TransitGatewayAttachmentId"]
        attachments_by_id[att_id] = dict(att)
        # Ensure VPC/subnet fields default to None/empty
        attachments_by_id[att_id].setdefault("VpcId", None)
        attachments_by_id[att_id].setdefault("SubnetIds", [])

    for vpc_att in tgw_vpc_attachments:
        att_id = vpc_att["TransitGatewayAttachmentId"]
        if att_id in attachments_by_id:
            attachments_by_id[att_id]["VpcId"] = vpc_att.get("VpcId")
            attachments_by_id[att_id]["SubnetIds"] = vpc_att.get("SubnetIds", [])
        else:
            vpc_att.setdefault("ResourceType", None)
            attachments_by_id[att_id] = dict(vpc_att)

    return list(attachments_by_id.values())


@timeit
def load_transit_gateways(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSTransitGatewaySchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_tgw_attachments(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSTransitGatewayAttachmentSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup_transit_gateways(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict,
) -> None:
    # Custom cleanup for TGW: the sub_resource RESOURCE rel points to OwnerId (per-record),
    # not AWS_ID (kwarg), so GraphJob.from_node_schema() can't scope cleanup correctly.
    # Instead, scope via RESOURCE|SHARED_WITH to the syncing account, matching both owned
    # and shared TGWs.
    run_write_query(
        neo4j_session,
        """
        MATCH (n:AWSTransitGateway)-[:RESOURCE|SHARED_WITH]-(:AWSAccount{id: $AWS_ID})
        WHERE n.lastupdated <> $UPDATE_TAG
        DETACH DELETE n
        """,
        **common_job_parameters,
    )
    GraphJob.from_node_schema(
        AWSTransitGatewayAttachmentSchema(), common_job_parameters
    ).run(neo4j_session)


def sync_transit_gateways(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict,
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
        tgw_attachments = get_tgw_attachments(boto3_session, region)
        tgw_vpc_attachments = get_tgw_vpc_attachments(boto3_session, region)
        transformed_attachments = transform_tgw_attachments(
            tgw_attachments,
            tgw_vpc_attachments,
        )
        load_tgw_attachments(
            neo4j_session,
            transformed_attachments,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup_transit_gateways(neo4j_session, common_job_parameters)
