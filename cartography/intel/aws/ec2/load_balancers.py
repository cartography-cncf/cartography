import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.intel.aws.util.boto3 import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_loadbalancer_data(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('elb', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_load_balancers')
    elbs: List[Dict] = []
    for page in paginator.paginate():
        elbs.extend(page['LoadBalancerDescriptions'])
    return elbs


@timeit
def load_load_balancer_listeners(
    neo4j_session: neo4j.Session, load_balancer_id: str, listener_data: List[Dict],
    update_tag: int,
) -> None:
    ingest_listener = """
    MATCH (elb:LoadBalancer{id: $LoadBalancerId})
    WITH elb
    UNWIND $Listeners as data
        MERGE (l:Endpoint:ELBListener{id: elb.id + toString(data.Listener.LoadBalancerPort) +
                toString(data.Listener.Protocol)})
        ON CREATE SET l.port = data.Listener.LoadBalancerPort, l.protocol = data.Listener.Protocol,
        l.firstseen = timestamp()
        SET l.instance_port = data.Listener.InstancePort, l.instance_protocol = data.Listener.InstanceProtocol,
        l.policy_names = data.PolicyNames,
        l.lastupdated = $update_tag
        WITH l, elb
        MERGE (elb)-[r:ELB_LISTENER]->(l)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $update_tag
    """

    neo4j_session.run(
        ingest_listener,
        LoadBalancerId=load_balancer_id,
        Listeners=listener_data,
        update_tag=update_tag,
    )


@timeit
def load_load_balancer_subnets(
    neo4j_session: neo4j.Session, load_balancer_id: str, subnets_data: List[Dict],
    update_tag: int,
) -> None:
    ingest_load_balancer_subnet = """
    MATCH (elb:LoadBalancer{id: $ID}), (subnet:EC2Subnet{subnetid: $SUBNET_ID})
    MERGE (elb)-[r:SUBNET]->(subnet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    for subnet_id in subnets_data:
        neo4j_session.run(
            ingest_load_balancer_subnet,
            ID=load_balancer_id,
            SUBNET_ID=subnet_id,
            update_tag=update_tag,
        )


@timeit
def load_load_balancers(
    neo4j_session: neo4j.Session, data: List[Dict], region: str, current_aws_account_id: str,
    update_tag: int,
) -> None:
    ingest_load_balancer = """
    MERGE (elb:LoadBalancer{id: $ID})
    ON CREATE SET elb.firstseen = timestamp(), elb.createdtime = $CREATED_TIME
    SET elb.lastupdated = $update_tag, elb.name = $NAME, elb.dnsname = $DNS_NAME,
    elb.canonicalhostedzonename = $HOSTED_ZONE_NAME, elb.canonicalhostedzonenameid = $HOSTED_ZONE_NAME_ID,
    elb.scheme = $SCHEME, elb.region = $Region
    WITH elb
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(elb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    ingest_load_balancersource_security_group = """
    MATCH (elb:LoadBalancer{id: $ID}),
    (group:EC2SecurityGroup{name: $GROUP_NAME})
    MERGE (elb)-[r:SOURCE_SECURITY_GROUP]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    ingest_load_balancer_security_group = """
    MATCH (elb:LoadBalancer{id: $ID}),
    (group:EC2SecurityGroup{groupid: $GROUP_ID})
    MERGE (elb)-[r:MEMBER_OF_EC2_SECURITY_GROUP]->(group)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    ingest_instances = """
    MATCH (elb:LoadBalancer{id: $ID}), (instance:EC2Instance{instanceid: $INSTANCE_ID})
    MERGE (elb)-[r:EXPOSE]->(instance)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    WITH instance
    MATCH (aa:AWSAccount{id: $AWS_ACCOUNT_ID})
    MERGE (aa)-[r:RESOURCE]->(instance)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    for lb in data:
        load_balancer_id = lb["DNSName"]

        neo4j_session.run(
            ingest_load_balancer,
            ID=load_balancer_id,
            CREATED_TIME=str(lb["CreatedTime"]),
            NAME=lb["LoadBalancerName"],
            DNS_NAME=load_balancer_id,
            HOSTED_ZONE_NAME=lb.get("CanonicalHostedZoneName"),
            HOSTED_ZONE_NAME_ID=lb.get("CanonicalHostedZoneNameID"),
            SCHEME=lb.get("Scheme", ""),
            AWS_ACCOUNT_ID=current_aws_account_id,
            Region=region,
            update_tag=update_tag,
        )

        if lb["Subnets"]:
            load_load_balancer_subnets(neo4j_session, load_balancer_id, lb["Subnets"], update_tag)

        if lb["SecurityGroups"]:
            for group in lb["SecurityGroups"]:
                neo4j_session.run(
                    ingest_load_balancer_security_group,
                    ID=load_balancer_id,
                    GROUP_ID=str(group),
                    update_tag=update_tag,
                )

        if lb["SourceSecurityGroup"]:
            source_group = lb["SourceSecurityGroup"]
            neo4j_session.run(
                ingest_load_balancersource_security_group,
                ID=load_balancer_id,
                GROUP_NAME=source_group["GroupName"],
                update_tag=update_tag,
            )

        if lb["Instances"]:
            for instance in lb["Instances"]:
                neo4j_session.run(
                    ingest_instances,
                    ID=load_balancer_id,
                    INSTANCE_ID=instance["InstanceId"],
                    AWS_ACCOUNT_ID=current_aws_account_id,
                    update_tag=update_tag,
                )

        if lb["ListenerDescriptions"]:
            load_load_balancer_listeners(neo4j_session, load_balancer_id, lb["ListenerDescriptions"], update_tag)


@timeit
def cleanup_load_balancers(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_ingest_load_balancers_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_load_balancers(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str], current_aws_account_id: str,
    update_tag: int, common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info("Syncing EC2 load balancers for region '%s' in account '%s'.", region, current_aws_account_id)
        data = get_loadbalancer_data(boto3_session, region)
        load_load_balancers(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_load_balancers(neo4j_session, common_job_parameters)
