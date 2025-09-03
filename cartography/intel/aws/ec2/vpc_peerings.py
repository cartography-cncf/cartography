import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.vpc import AWSVpcSchema
from cartography.models.aws.ec2.vpc_cidr import AWSIPv4CidrBlockSchema
from cartography.models.aws.ec2.vpc_peering import AWSAccountVPCPeeringSchema
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
) -> Tuple[
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Dict[str, Any]],
]:
    transformed_peerings: List[Dict[str, Any]] = []
    accepter_cidr_blocks: List[Dict[str, Any]] = []
    requester_cidr_blocks: List[Dict[str, Any]] = []
    vpc_nodes: List[Dict[str, Any]] = []

    for peering in vpc_peerings:
        accepter_cidr_ids: List[str] = []
        for c_b in peering.get("AccepterVpcInfo", {}).get("CidrBlockSet", []):
            block_id = f"{peering.get('AccepterVpcInfo', {}).get('VpcId')}|{c_b.get('CidrBlock')}"
            accepter_cidr_blocks.append(
                {
                    "Id": block_id,
                    "VpcId": peering.get("AccepterVpcInfo", {}).get("VpcId"),
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
            block_id = f"{peering.get('RequesterVpcInfo', {}).get('VpcId')}|{c_b.get('CidrBlock')}"
            requester_cidr_blocks.append(
                {
                    "Id": block_id,
                    "VpcId": peering.get("RequesterVpcInfo", {}).get("VpcId"),
                    "AssociationId": c_b.get("AssociationId"),
                    "CidrBlock": c_b.get("CidrBlock"),
                    "BlockState": c_b.get("CidrBlockState", {}).get("State"),
                    "BlockStateMessage": c_b.get("CidrBlockState", {}).get(
                        "StatusMessage",
                    ),
                },
            )
            requester_cidr_ids.append(block_id)

        # Create VPC nodes for accepter and requester VPCs
        accepter_vpc_id = peering.get("AccepterVpcInfo", {}).get("VpcId")
        accepter_owner_id = peering.get("AccepterVpcInfo", {}).get("OwnerId")
        if accepter_vpc_id:
            vpc_nodes.append(
                {
                    "VpcId": accepter_vpc_id,
                    "PrimaryCIDRBlock": None,  # VPCs from peering data don't have complete info
                    "InstanceTenancy": None,
                    "State": None,
                    "IsDefault": None,
                    "DhcpOptionsId": None,
                    "AccountId": accepter_owner_id,  # Account that owns this VPC
                }
            )

        requester_vpc_id = peering.get("RequesterVpcInfo", {}).get("VpcId")
        requester_owner_id = peering.get("RequesterVpcInfo", {}).get("OwnerId")
        if requester_vpc_id:
            vpc_nodes.append(
                {
                    "VpcId": requester_vpc_id,
                    "PrimaryCIDRBlock": None,  # VPCs from peering data don't have complete info
                    "InstanceTenancy": None,
                    "State": None,
                    "IsDefault": None,
                    "DhcpOptionsId": None,
                    "AccountId": requester_owner_id,  # Account that owns this VPC
                }
            )

        transformed_peerings.append(
            {
                "VpcPeeringConnectionId": peering.get("VpcPeeringConnectionId"),
                "AllowDnsResolutionFromRemoteVpc": peering.get(
                    "RequesterVpcInfo",
                    {},
                )
                .get("PeeringOptions", {})
                .get(
                    "AllowDnsResolutionFromRemoteVpc",
                ),
                "AllowEgressFromLocalClassicLinkToRemoteVpc": peering.get(
                    "RequesterVpcInfo",
                    {},
                )
                .get("PeeringOptions", {})
                .get(
                    "AllowEgressFromLocalClassicLinkToRemoteVpc",
                ),
                "AllowEgressFromLocalVpcToRemoteClassicLink": peering.get(
                    "RequesterVpcInfo",
                    {},
                )
                .get("PeeringOptions", {})
                .get(
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

    return transformed_peerings, accepter_cidr_blocks, requester_cidr_blocks, vpc_nodes


@timeit
def transform_aws_accounts_from_vpc_peering(
    vpc_peerings: List[Dict],
) -> List[Dict[str, Any]]:
    """
    Transform VPC peering data to extract AWS account information.
    Creates composite AWS account nodes with context from VPC peering.
    """
    account_data: Dict[str, Dict[str, Any]] = {}

    for peering in vpc_peerings:
        # Extract accepter account
        accepter_owner_id = peering.get("AccepterVpcInfo", {}).get("OwnerId")
        if accepter_owner_id:
            account_data[accepter_owner_id] = {
                "id": accepter_owner_id,
            }

        # Extract requester account
        requester_owner_id = peering.get("RequesterVpcInfo", {}).get("OwnerId")
        if requester_owner_id:
            account_data[requester_owner_id] = {
                "id": requester_owner_id,
            }

    return list(account_data.values())


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
def load_aws_accounts_from_vpc_peering(
    neo4j_session: neo4j.Session,
    aws_accounts: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Load AWS account nodes using the composite schema.
    This allows VPC peering data to provide additional context about AWS accounts.
    """
    load(
        neo4j_session,
        AWSAccountVPCPeeringSchema(),
        aws_accounts,
        lastupdated=update_tag,
    )


@timeit
def load_vpc_nodes(
    neo4j_session: neo4j.Session,
    vpc_nodes: List[Dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    # Group VPC nodes by their actual account ID
    vpc_nodes_by_account: Dict[str, List[Dict[str, Any]]] = {}
    for vpc in vpc_nodes:
        account_id = vpc.get(
            "AccountId", aws_account_id
        )  # Use VPC's own account or fallback
        if account_id not in vpc_nodes_by_account:
            vpc_nodes_by_account[account_id] = []
        vpc_nodes_by_account[account_id].append(vpc)

    # Load VPCs for each account separately
    for account_id, account_vpc_nodes in vpc_nodes_by_account.items():
        # Remove the AccountId field as it's not part of the VPC schema
        for vpc in account_vpc_nodes:
            vpc.pop("AccountId", None)

        load(
            neo4j_session,
            AWSVpcSchema(),
            account_vpc_nodes,
            lastupdated=update_tag,
            AWS_ID=account_id,
            Region=region,
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
        AWS_ID=aws_account_id,
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
        vpc_peerings, accepter_cidrs, requester_cidrs, vpc_nodes = (
            transform_vpc_peering_data(
                raw_data,
            )
        )
        aws_accounts = transform_aws_accounts_from_vpc_peering(raw_data)

        # Load AWS accounts first (composite pattern)
        load_aws_accounts_from_vpc_peering(
            neo4j_session,
            aws_accounts,
            update_tag,
        )

        load_vpc_nodes(
            neo4j_session,
            vpc_nodes,
            region,
            current_aws_account_id,
            update_tag,
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
