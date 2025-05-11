import logging

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.load_balancer_listeners import ELBListenerSchema
from cartography.models.aws.ec2.load_balancers import LoadBalancerSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


def _get_listener_id(load_balancer_id: str, port: int, protocol: str) -> str:
    """
    Generate a unique ID for a load balancer listener.

    Args:
        load_balancer_id: The ID of the load balancer
        port: The listener port
        protocol: The listener protocol

    Returns:
        A unique ID string for the listener
    """
    return f"{load_balancer_id}{port}{protocol}"


def transform_load_balancer_listener_data(
    load_balancer_id: str, listener_data: list[dict]
) -> list[dict]:
    """
    Transform load balancer listener data into a format suitable for cartography ingestion.

    Args:
        load_balancer_id: The ID of the load balancer
        listener_data: List of listener data from AWS API

    Returns:
        List of transformed listener data
    """
    transformed = []
    for listener in listener_data:
        listener_info = listener["Listener"]
        transformed_listener = {
            "id": _get_listener_id(
                load_balancer_id,
                listener_info["LoadBalancerPort"],
                listener_info["Protocol"],
            ),
            "port": listener_info.get("LoadBalancerPort"),
            "protocol": listener_info.get("Protocol"),
            "instance_port": listener_info.get("InstancePort"),
            "instance_protocol": listener_info.get("InstanceProtocol"),
            "policy_names": listener.get("PolicyNames", []),
            "LoadBalancerId": load_balancer_id,
        }
        transformed.append(transformed_listener)
    return transformed


def transform_load_balancer_data(
    load_balancers: list[dict],
) -> tuple[list[dict], list[dict]]:
    """
    Transform load balancer data into a format suitable for cartography ingestion.

    Args:
        load_balancers: List of load balancer data from AWS API

    Returns:
        Tuple of (transformed load balancer data, transformed listener data)
    """
    transformed = []
    listener_data = []

    for lb in load_balancers:
        load_balancer_id = lb["DNSName"]
        transformed_lb = {
            "id": load_balancer_id,
            "name": lb["LoadBalancerName"],
            "dnsname": lb["DNSName"],
            "canonicalhostedzonename": lb.get("CanonicalHostedZoneName"),
            "canonicalhostedzonenameid": lb.get("CanonicalHostedZoneNameID"),
            "scheme": lb.get("Scheme"),
            "createdtime": str(lb["CreatedTime"]),
            "GROUP_NAME": lb.get("SourceSecurityGroup", {}).get("GroupName"),
            "GROUP_IDS": [str(group) for group in lb.get("SecurityGroups", [])],
            "INSTANCE_IDS": [
                instance["InstanceId"] for instance in lb.get("Instances", [])
            ],
            "LISTENER_IDS": [
                _get_listener_id(
                    load_balancer_id,
                    listener["Listener"]["LoadBalancerPort"],
                    listener["Listener"]["Protocol"],
                )
                for listener in lb.get("ListenerDescriptions", [])
            ],
        }
        transformed.append(transformed_lb)

        # Classic ELB listeners are not returned anywhere else in AWS, so we must parse them out
        # of the describe_load_balancers response.
        if lb.get("ListenerDescriptions"):
            listener_data.extend(
                transform_load_balancer_listener_data(
                    load_balancer_id,
                    lb.get("ListenerDescriptions", []),
                ),
            )

    return transformed, listener_data


@timeit
@aws_handle_regions
def get_loadbalancer_data(
    boto3_session: boto3.session.Session, region: str
) -> list[dict]:
    client = boto3_session.client(
        "elb", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("describe_load_balancers")
    elbs: list[dict] = []
    for page in paginator.paginate():
        elbs.extend(page["LoadBalancerDescriptions"])
    return elbs


@timeit
def load_load_balancers(
    neo4j_session: neo4j.Session,
    data: list[dict],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        LoadBalancerSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_load_balancer_listeners(
    neo4j_session: neo4j.Session,
    data: list[dict],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ELBListenerSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup_load_balancers(
    neo4j_session: neo4j.Session, common_job_parameters: dict
) -> None:
    GraphJob.from_node_schema(ELBListenerSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(LoadBalancerSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_load_balancers(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    for region in regions:
        logger.info(
            "Syncing EC2 load balancers for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        data = get_loadbalancer_data(boto3_session, region)
        transformed_data, listener_data = transform_load_balancer_data(data)

        load_load_balancers(
            neo4j_session, transformed_data, region, current_aws_account_id, update_tag
        )
        load_load_balancer_listeners(
            neo4j_session, listener_data, region, current_aws_account_id, update_tag
        )

    cleanup_load_balancers(neo4j_session, common_job_parameters)
