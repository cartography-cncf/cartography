import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.vpc import AWSVpcSchema
from cartography.models.aws.ec2.vpc_cidr import AWSIPv4CidrBlockSchema
from cartography.models.aws.ec2.vpc_cidr import AWSIPv6CidrBlockSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_ec2_vpcs(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    client = boto3_session.client(
        "ec2",
        region_name=region,
        config=get_botocore_config(),
    )
    return client.describe_vpcs().get("Vpcs", [])


def transform_vpc_data(
    vpc_list: list[dict[str, Any]], region: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:

    vpc_data: list[dict[str, Any]] = []
    ipv4_cidr_blocks: list[dict[str, Any]] = []
    ipv6_cidr_blocks: list[dict[str, Any]] = []

    for vpc in vpc_list:
        vpc_record = {
            "VpcId": vpc.get("VpcId"),
            "InstanceTenancy": vpc.get("InstanceTenancy"),
            "State": vpc.get("State"),
            "IsDefault": vpc.get("IsDefault"),
            "PrimaryCIDRBlock": vpc.get("CidrBlock"),
            "DhcpOptionsId": vpc.get("DhcpOptionsId"),
            "lastupdated": vpc.get("lastupdated"),
        }
        vpc_data.append(vpc_record)

        ipv4_associations = vpc.get("CidrBlockAssociationSet", [])
        for association in ipv4_associations:
            ipv4_block = {
                "Id": vpc["VpcId"] + "|" + association.get("CidrBlock"),
                "VpcId": vpc["VpcId"],
                "AssociationId": association.get("AssociationId"),
                "CidrBlock": association.get("CidrBlock"),
                "BlockState": association.get("CidrBlockState", {}).get("State"),
                "BlockStateMessage": association.get("CidrBlockState", {}).get(
                    "StatusMessage"
                ),
            }
            ipv4_cidr_blocks.append(ipv4_block)

        ipv6_associations = vpc.get("Ipv6CidrBlockAssociationSet", [])
        for association in ipv6_associations:
            ipv6_block = {
                "Id": vpc["VpcId"] + "|" + association.get("Ipv6CidrBlock"),
                "VpcId": vpc["VpcId"],
                "AssociationId": association.get("AssociationId"),
                "CidrBlock": association.get("Ipv6CidrBlock"),
                "BlockState": association.get("Ipv6CidrBlockState", {}).get("State"),
                "BlockStateMessage": association.get("Ipv6CidrBlockState", {}).get(
                    "StatusMessage"
                ),
            }
            ipv6_cidr_blocks.append(ipv6_block)

    return vpc_data, ipv4_cidr_blocks, ipv6_cidr_blocks


@timeit
def load_ec2_vpcs(
    neo4j_session: neo4j.Session,
    vpcs: list[dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(vpcs)} EC2 VPCs for region '{region}' into graph.")
    # https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-vpcs.html
    # {
    #     "Vpcs": [
    #         {
    #             "VpcId": "vpc-a01106c2",
    #             "InstanceTenancy": "default",
    #             "Tags": [
    #                 {
    #                     "Value": "MyVPC",
    #                     "Key": "Name"
    #                 }
    #             ],
    #             "CidrBlockAssociations": [
    #                 {
    #                     "AssociationId": "vpc-cidr-assoc-a26a41ca",
    #                     "CidrBlock": "10.0.0.0/16",
    #                     "CidrBlockState": {
    #                         "State": "associated"
    #                     }
    #                 }
    #             ],
    #             "State": "available",
    #             "DhcpOptionsId": "dopt-7a8b9c2d",
    #             "CidrBlock": "10.0.0.0/16",
    #             "IsDefault": false
    #         }
    #     ]
    # }
    load(
        neo4j_session,
        AWSVpcSchema(),
        vpcs,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
    )


@timeit
def load_ipv4_cidr_blocks(
    neo4j_session: neo4j.Session,
    ipv4_cidr_blocks: list[dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSIPv4CidrBlockSchema(),
        ipv4_cidr_blocks,
        lastupdated=update_tag,
    )


@timeit
def load_ipv6_cidr_blocks(
    neo4j_session: neo4j.Session,
    ipv6_cidr_blocks: list[dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSIPv6CidrBlockSchema(),
        ipv6_cidr_blocks,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    GraphJob.from_node_schema(AWSIPv6CidrBlockSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(AWSIPv4CidrBlockSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(AWSVpcSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_vpc(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing EC2 VPC for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        raw_vpc_data = get_ec2_vpcs(boto3_session, region)
        vpc_data, ipv4_cidr_blocks, ipv6_cidr_blocks = transform_vpc_data(
            raw_vpc_data, region
        )
        load_ec2_vpcs(
            neo4j_session,
            vpc_data,
            region,
            current_aws_account_id,
            update_tag,
        )
        load_ipv4_cidr_blocks(
            neo4j_session,
            ipv4_cidr_blocks,
            region,
            current_aws_account_id,
            update_tag,
        )
        load_ipv6_cidr_blocks(
            neo4j_session,
            ipv6_cidr_blocks,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
