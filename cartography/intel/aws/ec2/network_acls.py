import logging
from collections import namedtuple
from typing import Any

import boto3
import neo4j

from .util import get_botocore_config
from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.network_acl_rules import EC2NetworkAclEgressRuleSchema
from cartography.models.aws.ec2.network_acl_rules import EC2NetworkAclInboundRuleSchema
from cartography.models.aws.ec2.network_acls import EC2NetworkAclSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)

Ec2AclObjects = namedtuple(
    "Ec2AclObjects", [
        'network_acls',
        'inbound_rules',
        'outbound_rules',
    ],
)


@timeit
@aws_handle_regions
def get_network_acl_data(boto3_session: boto3.session.Session, region: str) -> list[dict[str, Any]]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_network_acls')
    acls = []
    for page in paginator.paginate():
        acls.extend(page['NetworkAcls'])
    return acls


def transform_network_acl_data(
        data_list: list[dict[str, Any]],
        region: str,
        current_aws_account_id: str,
) -> Ec2AclObjects:
    network_acls = []
    inbound_rules = []
    outbound_rules = []

    for network_acl in data_list:
        network_acl_id = network_acl['NetworkAclId']
        base_network_acl = {
            'Id': network_acl_id,
            'Arn': f'arn:aws:ec2:{region}:{current_aws_account_id}:network-acl/{network_acl_id}',
            'IsDefault': network_acl['IsDefault'],
            'VpcId': network_acl['VpcId'],
            'OwnerId': network_acl['OwnerId'],
        }
        if network_acl.get('Associations') and network_acl['Associations']:
            # Include subnet associations in the data object if they exist
            for association in network_acl['Associations']:
                base_network_acl['NetworkAclAssociationId'] = association['NetworkAclAssociationId']
                base_network_acl['SubnetId'] = association['SubnetId']
                network_acls.append(base_network_acl)
        else:
            # Otherwise if there's no associations then don't include that in the data object
            network_acls.append(base_network_acl)

        if network_acl.get("Entries"):
            for rule in network_acl["Entries"]:
                direction = 'egress' if rule['Egress'] else 'inbound'
                transformed_rule = {
                    'Id': f"{network_acl['NetworkAclId']}/{direction}/{rule['RuleNumber']}",
                    'CidrBlock': rule.get('CidrBlock'),
                    'Ipv6CidrBlock': rule.get('Ipv6CidrBlock'),
                    'Egress': rule['Egress'],
                    'Protocol': rule['Protocol'],
                    'RuleAction': rule['RuleAction'],
                    'RuleNumber': rule['RuleNumber'],
                    # Add pointer back to the nacl to create an edge
                    'NetworkAclId': network_acl_id,
                    'FromPort': rule.get('PortRange', {}).get('FromPort'),
                    'ToPort': rule.get('PortRange', {}).get('ToPort'),
                }
                if transformed_rule['Egress']:
                    outbound_rules.append(transformed_rule)
                else:
                    inbound_rules.append(transformed_rule)
    return Ec2AclObjects(
        network_acls=network_acls,
        inbound_rules=inbound_rules,
        outbound_rules=outbound_rules,
    )


@timeit
def load_all_nacl_data(
        neo4j_session: neo4j.Session,
        ec2_acl_objects: Ec2AclObjects,
        region: str,
        aws_account_id: str,
        update_tag: int,
) -> None:
    load_network_acls(
        neo4j_session,
        ec2_acl_objects.network_acls,
        region,
        aws_account_id,
        update_tag,
    )
    load_network_acl_inbound_rules(
        neo4j_session,
        ec2_acl_objects.inbound_rules,
        region,
        aws_account_id,
        update_tag,
    )
    load_network_acl_egress_rules(
        neo4j_session,
        ec2_acl_objects.outbound_rules,
        region,
        aws_account_id,
        update_tag,
    )


@timeit
def load_network_acls(
        neo4j_session: neo4j.Session,
        data: list[dict[str, Any]],
        region: str,
        aws_account_id: str,
        update_tag: int,
) -> None:
    logger.info(f"Loading {len(data)} network acls in {region}.")
    load(
        neo4j_session,
        EC2NetworkAclSchema(),
        data,
        Region=region,
        AWS_ID=aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_network_acl_inbound_rules(
        neo4j_session: neo4j.Session,
        data: list[dict[str, Any]],
        region: str,
        aws_account_id: str,
        update_tag: int,
) -> None:
    logger.info(f"Loading {len(data)} network acl inbound rules in {region}.")
    load(
        neo4j_session,
        EC2NetworkAclInboundRuleSchema(),
        data,
        Region=region,
        AWS_ID=aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_network_acl_egress_rules(
        neo4j_session: neo4j.Session,
        data: list[dict[str, Any]],
        region: str,
        aws_account_id: str,
        update_tag: int,
) -> None:
    logger.info(f"Loading {len(data)} network acl egress rules in {region}.")
    load(
        neo4j_session,
        EC2NetworkAclEgressRuleSchema(),
        data,
        Region=region,
        AWS_ID=aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup_network_acls(neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    GraphJob.from_node_schema(EC2NetworkAclSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(EC2NetworkAclInboundRuleSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(EC2NetworkAclEgressRuleSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_network_acls(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        regions: list[str],
        current_aws_account_id: str,
        update_tag: int,
        common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        logger.info(f"Syncing EC2 network ACLs for region '{region}' in account '{current_aws_account_id}'.")
        data = get_network_acl_data(boto3_session, region)
        ec2_acl_data = transform_network_acl_data(data, region, current_aws_account_id)
        load_all_nacl_data(
            neo4j_session,
            ec2_acl_data,
            region,
            current_aws_account_id,
            update_tag,
        )
        cleanup_network_acls(neo4j_session, common_job_parameters)
