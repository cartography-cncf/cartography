import logging
import re
from collections import namedtuple
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from .util import get_botocore_config
from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.networkinterfaces import EC2NetworkInterfaceSchema
from cartography.models.aws.ec2.privateip_networkinterface import EC2PrivateIpNetworkInterfaceSchema
from cartography.models.aws.ec2.securitygroup_networkinterface import EC2SecurityGroupNetworkInterfaceSchema
from cartography.models.aws.ec2.subnet_networkinterface import EC2SubnetNetworkInterfaceSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

Ec2NetworkData = namedtuple(
    "Ec2NetworkData", [
        "network_interface_list",
        "private_ip_list",
        "sg_list",
        "subnet_list",
    ],
)


@timeit
@aws_handle_regions
def get_network_interface_data(boto3_session: boto3.session.Session, region: str) -> List[Dict[str, Any]]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_network_interfaces')
    subnets: List[Dict] = []
    for page in paginator.paginate():
        subnets.extend(page['NetworkInterfaces'])
    return subnets


def transform_network_interface_data(data_list: List[Dict[str, Any]], region: str) -> Ec2NetworkData:
    network_interface_list = []
    private_ip_list = []
    sg_list = []
    subnet_list = []

    for network_interface in data_list:
        # Parse network interface description for ELB association
        # https://aws.amazon.com/premiumsupport/knowledge-center/elb-find-load-balancer-IP/
        elb_v1_id = None
        elb_v2_id = None
        elb_match = re.match(r'^ELB (?:net|app)/([^\/]+)\/(.*)', network_interface.get('Description', ''))
        if elb_match:
            elb_v1_id = f'{elb_match[1]}-{elb_match[2]}.elb.{region}.amazonaws.com'
        else:
            elb_match = re.match(r'^ELB (.*)', network_interface.get('Description', ''))
            if elb_match:
                elb_v2_id = elb_match[1]
        # TODO issue #1024 change this to arn when ready
        network_interface_id = network_interface['NetworkInterfaceId']
        network_interface_list.append(
            {
                'Id': network_interface_id,
                'NetworkInterfaceId': network_interface['NetworkInterfaceId'],
                'Description': network_interface['Description'],
                'InstanceId': network_interface.get('Attachment', {}).get('InstanceId'),
                'InterfaceType': network_interface['InterfaceType'],
                'MacAddress': network_interface['MacAddress'],
                'PrivateDnsName': network_interface.get('PrivateDnsName'),
                'PrivateIpAddress': network_interface['PrivateIpAddress'],
                'PublicIp': network_interface.get('Association', {}).get('PublicIp'),
                'RequesterId': network_interface.get('RequesterId'),
                'RequesterManaged': network_interface['RequesterManaged'],
                'SourceDestCheck': network_interface['SourceDestCheck'],
                'Status': network_interface['Status'],
                'SubnetId': network_interface['SubnetId'],
                'ElbV1Id': elb_v1_id,
                'ElbV2Id': elb_v2_id,
            },
        )
        if network_interface.get('PrivateIpAddresses'):
            for private_ip_address in network_interface['PrivateIpAddresses']:
                private_ip_list.append(
                    {
                        'Id': f"{network_interface['NetworkInterfaceId']}:{private_ip_address['PrivateIpAddress']}",
                        'NetworkInterfaceId': network_interface['NetworkInterfaceId'],
                        'IpOwnerId': private_ip_address.get('Association', {}).get('IpOwnerId'),
                        'Primary': private_ip_address['Primary'],
                        'PrivateIpAddress': private_ip_address['PrivateIpAddress'],
                        'PublicIp': private_ip_address.get('Association', {}).get('PublicIp'),
                    },
                )

        if network_interface.get("Groups"):
            for group in network_interface["Groups"]:
                sg_list.append(
                    {
                        'GroupId': group['GroupId'],
                        'NetworkInterfaceId': network_interface_id,
                    },
                )

        subnet_id = network_interface.get('SubnetId')
        if subnet_id:
            subnet_list.append(
                {
                    'NetworkInterfaceId': network_interface_id,
                    'SubnetId': subnet_id,
                    'ElbV1Id': elb_v1_id,
                    'ElbV2Id': elb_v2_id,
                },
            )

    return Ec2NetworkData(
        network_interface_list=network_interface_list,
        private_ip_list=private_ip_list,
        sg_list=sg_list,
        subnet_list=subnet_list,
    )


@timeit
def load_network_interfaces(
        neo4j_session: neo4j.Session,
        data: List[Dict[str, Any]],
        region: str,
        aws_account_id: str,
        update_tag: int,
) -> None:
    logger.info(f"Loading {len(data)} network interfaces in {region}.")
    load(
        neo4j_session,
        EC2NetworkInterfaceSchema(),
        data,
        Region=region,
        AWS_ID=aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_private_ip_network_interface(
        neo4j_session: neo4j.Session,
        data: List[Dict[str, Any]],
        region: str,
        aws_account_id: str,
        update_tag: int,
) -> None:
    """
    Private IPs as known by describe-network-interfaces.
    """
    logger.info(f"Loading {len(data)} private IPs in {region}.")
    load(
        neo4j_session,
        EC2PrivateIpNetworkInterfaceSchema(),
        data,
        Region=region,
        AWS_ID=aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_security_group_network_interface(
        neo4j_session: neo4j.Session,
        data: List[Dict[str, Any]],
        region: str,
        aws_account_id: str,
        update_tag: int,
) -> None:
    """
    Security groups as known by describe-network-interfaces.
    """
    logger.info(f"Loading {len(data)} security groups in {region}.")
    load(
        neo4j_session,
        EC2SecurityGroupNetworkInterfaceSchema(),
        data,
        Region=region,
        AWS_ID=aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_subnet_network_interface(
        neo4j_session: neo4j.Session,
        data: List[Dict[str, Any]],
        region: str,
        aws_account_id: str,
        update_tag: int,
) -> None:
    """
    Subnets as known by describe-network-interfaces.
    """
    logger.info(f"Loading {len(data)} subnets in {region}.")
    load(
        neo4j_session,
        EC2SubnetNetworkInterfaceSchema(),
        data,
        Region=region,
        AWS_ID=aws_account_id,
        lastupdated=update_tag,
    )


def load_network_data(
        neo4j_session: neo4j.Session,
        region: str,
        current_aws_account_id: str,
        update_tag: int,
        network_interface_list: List[Dict[str, Any]],
        private_ip_list: List[Dict[str, Any]],
        subnet_list: List[Dict[str, Any]],
        sg_list: List[Dict[str, Any]],
) -> None:
    load_network_interfaces(neo4j_session, network_interface_list, region, current_aws_account_id, update_tag)
    load_private_ip_network_interface(neo4j_session, private_ip_list, region, current_aws_account_id, update_tag)
    load_subnet_network_interface(neo4j_session, subnet_list, region, current_aws_account_id, update_tag)
    load_security_group_network_interface(neo4j_session, sg_list, region, current_aws_account_id, update_tag)


@timeit
def cleanup_network_interfaces(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    GraphJob.from_node_schema(EC2NetworkInterfaceSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(EC2PrivateIpNetworkInterfaceSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_network_interfaces(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        regions: List[str],
        current_aws_account_id: str,
        update_tag: int,
        common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info(f"Syncing EC2 network interfaces for region '{region}' in account '{current_aws_account_id}'.")
        data = get_network_interface_data(boto3_session, region)
        ec2_network_data = transform_network_interface_data(data, region)
        load_network_data(
            neo4j_session,
            region,
            current_aws_account_id,
            update_tag,
            ec2_network_data.network_interface_list,
            ec2_network_data.private_ip_list,
            ec2_network_data.subnet_list,
            ec2_network_data.sg_list,
        )
    cleanup_network_interfaces(neo4j_session, common_job_parameters)
