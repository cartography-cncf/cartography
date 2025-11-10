import logging
from typing import Dict
from typing import List

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import run_write_query
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

from .util import get_botocore_config

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


@timeit
def load_transit_gateways(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    ingest_transit_gateway = """
    MERGE (ownerAccount:AWSAccount {id: $OwnerId})
    ON CREATE SET ownerAccount.firstseen = timestamp()
    SET ownerAccount.lastupdated = $update_tag

    MERGE (tgw:AWSTransitGateway {id: $ARN})
    ON CREATE SET tgw.firstseen = timestamp(), tgw.arn = $ARN
    SET tgw.tgw_id = $TgwId,
    tgw.ownerid = $OwnerId,
    tgw.state = $State,
    tgw.description = $Description,
    tgw.region = $Region,
    tgw.lastupdated = $update_tag

    WITH tgw
    MERGE (ownerAccount)-[r:RESOURCE]->(tgw)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    for tgw in data:
        tgw_id = tgw["TransitGatewayId"]

        run_write_query(
            neo4j_session,
            ingest_transit_gateway,
            TgwId=tgw_id,
            ARN=tgw["TransitGatewayArn"],
            Description=tgw.get("Description"),
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            OwnerId=tgw["OwnerId"],
            State=tgw["State"],
            update_tag=update_tag,
        )
        _attach_shared_transit_gateway(
            neo4j_session,
            tgw,
            region,
            current_aws_account_id,
            update_tag,
        )


@timeit
def _attach_shared_transit_gateway(
    neo4j_session: neo4j.Session,
    tgw: Dict,
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    attach_tgw = """
    MERGE (tgw:AWSTransitGateway {id: $ARN})
    ON CREATE SET tgw.firstseen = timestamp()
    SET tgw.lastupdated = $update_tag

    WITH tgw
    MATCH (currentAccount:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (tgw)-[s:SHARED_WITH]->(currentAccount)
    ON CREATE SET s.firstseen = timestamp()
    SET s.lastupdated = $update_tag
    """

    if tgw["OwnerId"] != current_aws_account_id:
        run_write_query(
            neo4j_session,
            attach_tgw,
            ARN=tgw["TransitGatewayArn"],
            TransitGatewayId=tgw["TransitGatewayId"],
            AWS_ACCOUNT_ID=current_aws_account_id,
            update_tag=update_tag,
        )


@timeit
def load_tgw_attachments(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    ingest_transit_gateway = """
    MERGE (tgwa:AWSTransitGatewayAttachment{id: $TgwAttachmentId})
    ON CREATE SET tgwa.firstseen = timestamp()
    SET tgwa.region = $Region,
    tgwa.resource_type = $ResourceType,
    tgwa.state = $State,
    tgwa.lastupdated = $update_tag

    WITH tgwa
    MATCH (awsAccount:AWSAccount {id: $AWS_ACCOUNT_ID})
    MERGE (awsAccount)-[r:RESOURCE]->(tgwa)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag

    WITH tgwa
    MATCH (tgw:AWSTransitGateway {tgw_id: $TransitGatewayId})
    MERGE (tgwa)-[attach:ATTACHED_TO]->(tgw)
    ON CREATE SET attach.firstseen = timestamp()
    SET attach.lastupdated = $update_tag
    """

    for tgwa in data:
        tgwa_id = tgwa["TransitGatewayAttachmentId"]

        run_write_query(
            neo4j_session,
            ingest_transit_gateway,
            TgwAttachmentId=tgwa_id,
            TransitGatewayId=tgwa["TransitGatewayId"],
            ResourceId=tgwa.get("ResourceId"),
            Region=region,
            AWS_ACCOUNT_ID=current_aws_account_id,
            ResourceType=tgwa.get("ResourceType"),
            State=tgwa["State"],
            update_tag=update_tag,
        )

        if tgwa.get(
            "VpcId",
        ):  # only attach if the TGW attachment is a VPC TGW attachment
            _attach_tgw_vpc_attachment_to_vpc_subnets(
                neo4j_session,
                tgwa,
                region,
                current_aws_account_id,
                update_tag,
            )


@timeit
def _attach_tgw_vpc_attachment_to_vpc_subnets(
    neo4j_session: neo4j.Session,
    tgw_vpc_attachment: Dict,
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Attach a VPC Transit Gateway Attachment to the VPC and and subnets
    """
    attach_vpc_tgw_attachment_to_vpc = """
    MERGE (vpc:AWSVpc {id: $VpcId})
    ON CREATE SET vpc.firstseen = timestamp()
    SET vpc.lastupdated = $update_tag

    WITH vpc
    MATCH (tgwa:AWSTransitGatewayAttachment {id: $TgwAttachmentId})
    MERGE (vpc)-[r:RESOURCE]->(tgwa)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    attach_vpc_tgw_attachment_to_subnet = """
    MERGE (sub:EC2Subnet {subnetid: $SubnetId})
    ON CREATE SET sub.firstseen = timestamp()
    SET sub.lastupdated = $update_tag

    WITH sub
    MATCH (tgwa:AWSTransitGatewayAttachment {id: $TgwAttachmentId})
    MERGE (tgwa)-[p:PART_OF_SUBNET]->(sub)
    ON CREATE SET p.firstseen = timestamp()
    SET p.lastupdated = $update_tag
    """

    run_write_query(
        neo4j_session,
        attach_vpc_tgw_attachment_to_vpc,
        VpcId=tgw_vpc_attachment["VpcId"],
        TgwAttachmentId=tgw_vpc_attachment["TransitGatewayAttachmentId"],
        update_tag=update_tag,
    )

    for subnet_id in tgw_vpc_attachment["SubnetIds"]:
        run_write_query(
            neo4j_session,
            attach_vpc_tgw_attachment_to_subnet,
            SubnetId=subnet_id,
            TgwAttachmentId=tgw_vpc_attachment["TransitGatewayAttachmentId"],
            update_tag=update_tag,
        )


@timeit
def cleanup_transit_gateways(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    run_cleanup_job("aws_import_tgw_cleanup.json", neo4j_session, common_job_parameters)


def sync_transit_gateways(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info(
            "Syncing AWS Transit Gateways for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        tgws = get_transit_gateways(boto3_session, region)
        load_transit_gateways(
            neo4j_session,
            tgws,
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
        load_tgw_attachments(
            neo4j_session,
            tgw_attachments + tgw_vpc_attachments,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup_transit_gateways(neo4j_session, common_job_parameters)
