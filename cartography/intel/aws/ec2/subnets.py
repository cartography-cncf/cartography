import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from .util import get_botocore_config
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.auto_scaling_groups import EC2SubnetAutoScalingGroupSchema
from cartography.models.aws.ec2.subnet_instance import EC2SubnetInstanceSchema
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_subnet_data(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_subnets')
    subnets: List[Dict] = []
    for page in paginator.paginate():
        subnets.extend(page['Subnets'])
    return subnets


@timeit
def load_subnets(
    neo4j_session: neo4j.Session, data: List[Dict], region: str, aws_account_id: str,
    aws_update_tag: int,
) -> None:

    ingest_subnets = """
    UNWIND $subnets as subnet
    MERGE (snet:EC2Subnet{subnetid: subnet.SubnetId})
    ON CREATE SET snet.firstseen = timestamp()
    SET snet.lastupdated = $aws_update_tag, snet.name = subnet.CidrBlock, snet.cidr_block = subnet.CidrBlock,
    snet.available_ip_address_count = subnet.AvailableIpAddressCount, snet.default_for_az = subnet.DefaultForAz,
    snet.map_customer_owned_ip_on_launch = subnet.MapCustomerOwnedIpOnLaunch,
    snet.state = subnet.State, snet.assignipv6addressoncreation = subnet.AssignIpv6AddressOnCreation,
    snet.map_public_ip_on_launch = subnet.MapPublicIpOnLaunch, snet.subnet_arn = subnet.SubnetArn,
    snet.availability_zone = subnet.AvailabilityZone, snet.availability_zone_id = subnet.AvailabilityZoneId,
    snet.subnetid = subnet.SubnetId
    """

    ingest_subnet_vpc_relations = """
    UNWIND $subnets as subnet
    MATCH (snet:EC2Subnet{subnetid: subnet.SubnetId}), (vpc:AWSVpc{id: subnet.VpcId})
    MERGE (snet)-[r:MEMBER_OF_AWS_VPC]->(vpc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    ingest_subnet_aws_account_relations = """
    UNWIND $subnets as subnet
    MATCH (snet:EC2Subnet{subnetid: subnet.SubnetId}), (aws:AWSAccount{id: $aws_account_id})
    MERGE (aws)-[r:RESOURCE]->(snet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag
    """

    neo4j_session.run(
        ingest_subnets, subnets=data, aws_update_tag=aws_update_tag,
        region=region, aws_account_id=aws_account_id,
    )
    neo4j_session.run(
        ingest_subnet_vpc_relations, subnets=data, aws_update_tag=aws_update_tag,
        region=region, aws_account_id=aws_account_id,
    )
    neo4j_session.run(
        ingest_subnet_aws_account_relations, subnets=data, aws_update_tag=aws_update_tag,
        region=region, aws_account_id=aws_account_id,
    )


@timeit
def cleanup_subnets(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_ingest_subnets_cleanup.json', neo4j_session, common_job_parameters)
    GraphJob.from_node_schema(EC2SubnetInstanceSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(EC2SubnetAutoScalingGroupSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_subnets(
        neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
        current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing EC2 subnets for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_subnet_data(boto3_session, region)
        load_subnets(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_subnets(neo4j_session, common_job_parameters)
