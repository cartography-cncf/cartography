import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
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
def load_vpc_peerings(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    ingest_vpc_peerings = """
    UNWIND $vpc_peerings AS vpc_peering

    MERGE (pcx:AWSPeeringConnection{id: vpc_peering.VpcPeeringConnectionId})
    ON CREATE SET pcx.firstseen = timestamp()
    SET pcx.lastupdated = $update_tag,
    pcx.allow_dns_resolution_from_remote_vpc =
        vpc_peering.RequesterVpcInfo.PeeringOptions.AllowDnsResolutionFromRemoteVpc,
    pcx.allow_egress_from_local_classic_link_to_remote_vpc =
        vpc_peering.RequesterVpcInfo.PeeringOptions.AllowEgressFromLocalClassicLinkToRemoteVpc,
    pcx.allow_egress_from_local_vpc_to_remote_classic_link =
        vpc_peering.RequesterVpcInfo.PeeringOptions.AllowEgressFromLocalVpcToRemoteClassicLink,
    pcx.requester_region = vpc_peering.RequesterVpcInfo.Region,
    pcx.accepter_region = vpc_peering.AccepterVpcInfo.Region,
    pcx.status_code = vpc_peering.Status.Code,
    pcx.status_message = vpc_peering.Status.Message

    MERGE (avpc:AWSVpc{id: vpc_peering.AccepterVpcInfo.VpcId})
    ON CREATE SET avpc.firstseen = timestamp()
    SET avpc.lastupdated = $update_tag, avpc.vpcid = vpc_peering.AccepterVpcInfo.VpcId

    MERGE (rvpc:AWSVpc{id: vpc_peering.RequesterVpcInfo.VpcId})
    ON CREATE SET rvpc.firstseen = timestamp()
    SET rvpc.lastupdated = $update_tag, rvpc.vpcid = vpc_peering.RequesterVpcInfo.VpcId

    MERGE (aaccount:AWSAccount{id: vpc_peering.AccepterVpcInfo.OwnerId})
    ON CREATE SET aaccount.firstseen = timestamp()
    SET aaccount.lastupdated = $update_tag

    MERGE (raccount:AWSAccount{id: vpc_peering.RequesterVpcInfo.OwnerId})
    ON CREATE SET raccount.firstseen = timestamp()
    SET raccount.lastupdated = $update_tag

    MERGE (pcx)-[rav:ACCEPTER_VPC]->(avpc)
    ON CREATE SET rav.firstseen = timestamp()
    SET rav.lastupdated = $update_tag

    MERGE (aaccount)-[ra:RESOURCE]->(avpc)
    ON CREATE SET ra.firstseen = timestamp()
    SET ra.lastupdated = $update_tag

    MERGE (pcx)-[rrv:REQUESTER_VPC]->(rvpc)
    ON CREATE SET rrv.firstseen = timestamp()
    SET rrv.lastupdated = $update_tag

    MERGE (raccount)-[rr:RESOURCE]->(rvpc)
    ON CREATE SET rr.firstseen = timestamp()
    SET rr.lastupdated = $update_tag

    """

    neo4j_session.run(
        ingest_vpc_peerings,
        vpc_peerings=data,
        update_tag=update_tag,
        region=region,
        aws_account_id=aws_account_id,
    )


@timeit
def load_accepter_cidrs(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:

    ingest_accepter_cidr = """
    UNWIND $vpc_peerings AS vpc_peering
    UNWIND vpc_peering.AccepterVpcInfo.CidrBlockSet AS c_b

    MERGE (ac_b:AWSCidrBlock:AWSIpv4CidrBlock{id: vpc_peering.AccepterVpcInfo.VpcId + '|' + c_b.CidrBlock})
    ON CREATE SET ac_b.firstseen = timestamp()
    SET ac_b.lastupdated = $update_tag, ac_b.cidr_block  =  c_b.CidrBlock

    WITH vpc_peering, ac_b
    MATCH (pcx:AWSPeeringConnection{id: vpc_peering.VpcPeeringConnectionId}), (cb:AWSCidrBlock{id: ac_b.id})
    MERGE (pcx)-[r:ACCEPTER_CIDR]->(cb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag

    WITH vpc_peering, ac_b
    MATCH (vpc:AWSVpc{id: vpc_peering.AccepterVpcInfo.VpcId}), (cb:AWSCidrBlock{id: ac_b.id})
    MERGE (vpc)-[r:BLOCK_ASSOCIATION]->(cb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    neo4j_session.run(
        ingest_accepter_cidr,
        vpc_peerings=data,
        update_tag=update_tag,
        region=region,
        aws_account_id=aws_account_id,
    )


@timeit
def load_requester_cidrs(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:

    ingest_requester_cidr = """
    UNWIND $vpc_peerings AS vpc_peering
    UNWIND vpc_peering.RequesterVpcInfo.CidrBlockSet AS c_b

    MERGE (rc_b:AWSCidrBlock:AWSIpv4CidrBlock{id: vpc_peering.RequesterVpcInfo.VpcId + '|' + c_b.CidrBlock})
    ON CREATE SET rc_b.firstseen = timestamp()
    SET rc_b.lastupdated = $update_tag, rc_b.cidr_block  =  c_b.CidrBlock

    WITH vpc_peering, rc_b
    MATCH (pcx:AWSPeeringConnection{id: vpc_peering.VpcPeeringConnectionId}), (cb:AWSCidrBlock{id: rc_b.id})
    MERGE (pcx)-[r:REQUESTER_CIDR]->(cb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag

    WITH vpc_peering, rc_b
    MATCH (vpc:AWSVpc{id: vpc_peering.RequesterVpcInfo.VpcId}), (cb:AWSCidrBlock{id: rc_b.id})
    MERGE (vpc)-[r:BLOCK_ASSOCIATION]->(cb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    neo4j_session.run(
        ingest_requester_cidr,
        vpc_peerings=data,
        update_tag=update_tag,
        region=region,
        aws_account_id=aws_account_id,
    )


@timeit
def cleanup_vpc_peerings(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    run_cleanup_job(
        "aws_import_vpc_peering_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


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
        data = get_vpc_peerings_data(boto3_session, region)
        load_vpc_peerings(
            neo4j_session,
            data,
            region,
            current_aws_account_id,
            update_tag,
        )
        load_accepter_cidrs(
            neo4j_session,
            data,
            region,
            current_aws_account_id,
            update_tag,
        )
        load_requester_cidrs(
            neo4j_session,
            data,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup_vpc_peerings(neo4j_session, common_job_parameters)
