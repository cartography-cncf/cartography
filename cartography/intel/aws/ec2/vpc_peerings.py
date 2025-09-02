import logging
from typing import Any, Dict, List, Tuple

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.vpc_cidr import AWSIPv4CidrBlockSchema
from cartography.models.aws.ec2.vpc_peering import AWSPeeringConnectionSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_vpc_peerings_data(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
    client = boto3_session.client(
        "ec2",
        region_name=region,
        config=get_botocore_config(),
    )
    return client.describe_vpc_peering_connections()["VpcPeeringConnections"]


@timeit
def transform_vpc_peering_data(
    vpc_peerings: List[Dict],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    transformed_peerings: List[Dict[str, Any]] = []
    accepter_cidr_blocks: List[Dict[str, Any]] = []
    requester_cidr_blocks: List[Dict[str, Any]] = []

    for peering in vpc_peerings:
        accepter_cidr_ids: List[str] = []
        for c_b in peering.get("AccepterVpcInfo", {}).get("CidrBlockSet", []):
            block_id = (
                f"{peering['AccepterVpcInfo']['VpcId']}|{c_b.get('CidrBlock')}"
            )
            accepter_cidr_blocks.append(
                {
                    "Id": block_id,
                    "VpcId": peering["AccepterVpcInfo"].get("VpcId"),
                    "AssociationId": c_b.get("AssociationId"),
                    "CidrBlock": c_b.get("CidrBlock"),
                    "BlockState": c_b.get("CidrBlockState", {}).get("State"),
                    "BlockStateMessage": c_b.get("CidrBlockState", {}).get(
                        "StatusMessage",
                    ),
                },
            )
            accepter_cidr_ids.append(block_id)

        requester_cidr_ids: List[str] = []
        for c_b in peering.get("RequesterVpcInfo", {}).get("CidrBlockSet", []):
            block_id = (
                f"{peering['RequesterVpcInfo']['VpcId']}|{c_b.get('CidrBlock')}"
            )
            requester_cidr_blocks.append(
                {
                    "Id": block_id,
                    "VpcId": peering["RequesterVpcInfo"].get("VpcId"),
                    "AssociationId": c_b.get("AssociationId"),
                    "CidrBlock": c_b.get("CidrBlock"),
                    "BlockState": c_b.get("CidrBlockState", {}).get("State"),
                    "BlockStateMessage": c_b.get("CidrBlockState", {}).get(
                        "StatusMessage",
                    ),
                },
            )
            requester_cidr_ids.append(block_id)

        transformed_peerings.append(
            {
                "VpcPeeringConnectionId": peering.get("VpcPeeringConnectionId"),
                "AllowDnsResolutionFromRemoteVpc": peering.get(
                    "RequesterVpcInfo",
                    {},
                ).get("PeeringOptions", {}).get(
                    "AllowDnsResolutionFromRemoteVpc",
                ),
                "AllowEgressFromLocalClassicLinkToRemoteVpc": peering.get(
                    "RequesterVpcInfo",
                    {},
                ).get("PeeringOptions", {}).get(
                    "AllowEgressFromLocalClassicLinkToRemoteVpc",
                ),
                "AllowEgressFromLocalVpcToRemoteClassicLink": peering.get(
                    "RequesterVpcInfo",
                    {},
                ).get("PeeringOptions", {}).get(
                    "AllowEgressFromLocalVpcToRemoteClassicLink",
                ),
                "RequesterRegion": peering.get("RequesterVpcInfo", {}).get(
                    "Region",
                ),
                "AccepterRegion": peering.get("AccepterVpcInfo", {}).get(
                    "Region",
                ),
                "StatusCode": peering.get("Status", {}).get("Code"),
                "StatusMessage": peering.get("Status", {}).get("Message"),
                "AccepterVpcId": peering.get("AccepterVpcInfo", {}).get("VpcId"),
                "RequesterVpcId": peering.get("RequesterVpcInfo", {}).get(
                    "VpcId",
                ),
                "ACCEPTER_CIDR_BLOCK_IDS": accepter_cidr_ids,
                "REQUESTER_CIDR_BLOCK_IDS": requester_cidr_ids,
            },
        )

    return transformed_peerings, accepter_cidr_blocks, requester_cidr_blocks


@timeit
def load_accepter_cidrs(
    neo4j_session: neo4j.Session,
    accepter_cidrs: List[Dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSIPv4CidrBlockSchema(),
        accepter_cidrs,
        lastupdated=update_tag,
    )


@timeit
def load_requester_cidrs(
    neo4j_session: neo4j.Session,
    requester_cidrs: List[Dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSIPv4CidrBlockSchema(),
        requester_cidrs,
        lastupdated=update_tag,
    )


@timeit
def load_vpc_peerings(
    neo4j_session: neo4j.Session,
    vpc_peerings: List[Dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSPeeringConnectionSchema(),
        vpc_peerings,
        lastupdated=update_tag,
    )


@timeit
def cleanup_vpc_peerings(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    GraphJob.from_node_schema(
        AWSPeeringConnectionSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_vpc_peerings(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.debug(
            "Syncing EC2 VPC peering for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        raw_data = get_vpc_peerings_data(boto3_session, region)
        vpc_peerings, accepter_cidrs, requester_cidrs = transform_vpc_peering_data(
            raw_data,
        )
        load_accepter_cidrs(
            neo4j_session,
            accepter_cidrs,
            region,
            current_aws_account_id,
            update_tag,
        )
        load_requester_cidrs(
            neo4j_session,
            requester_cidrs,
            region,
            current_aws_account_id,
            update_tag,
        )
        load_vpc_peerings(
            neo4j_session,
            vpc_peerings,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup_vpc_peerings(neo4j_session, common_job_parameters)
