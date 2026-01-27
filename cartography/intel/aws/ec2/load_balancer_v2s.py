import logging
from typing import Dict
from typing import List
from typing import Tuple

import boto3
import botocore
import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.loadbalancerv2 import ELBV2ListenerSchema
from cartography.models.aws.ec2.loadbalancerv2 import LoadBalancerV2Schema
from cartography.models.aws.ec2.loadbalancerv2 import LoadBalancerV2ToAWSLambdaMatchLink
from cartography.models.aws.ec2.loadbalancerv2 import (
    LoadBalancerV2ToEC2InstanceMatchLink,
)
from cartography.models.aws.ec2.loadbalancerv2 import (
    LoadBalancerV2ToEC2PrivateIpMatchLink,
)
from cartography.models.aws.ec2.loadbalancerv2 import (
    LoadBalancerV2ToLoadBalancerV2MatchLink,
)
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_load_balancer_v2_listeners(
    client: botocore.client.BaseClient,
    load_balancer_arn: str,
) -> List[Dict]:
    paginator = client.get_paginator("describe_listeners")
    listeners: List[Dict] = []
    for page in paginator.paginate(LoadBalancerArn=load_balancer_arn):
        listeners.extend(page["Listeners"])

    return listeners


@timeit
def get_load_balancer_v2_target_groups(
    client: botocore.client.BaseClient,
    load_balancer_arn: str,
) -> List[Dict]:
    paginator = client.get_paginator("describe_target_groups")
    target_groups: List[Dict] = []
    for page in paginator.paginate(LoadBalancerArn=load_balancer_arn):
        target_groups.extend(page["TargetGroups"])

    # Add instance data
    for target_group in target_groups:
        target_group["Targets"] = []
        target_health = client.describe_target_health(
            TargetGroupArn=target_group["TargetGroupArn"],
        )
        for target_health_description in target_health["TargetHealthDescriptions"]:
            target_group["Targets"].append(target_health_description["Target"]["Id"])

    return target_groups


@timeit
@aws_handle_regions
def get_loadbalancer_v2_data(boto3_session: boto3.Session, region: str) -> List[Dict]:
    client = boto3_session.client(
        "elbv2",
        region_name=region,
        config=get_botocore_config(),
    )
    paginator = client.get_paginator("describe_load_balancers")
    elbv2s: List[Dict] = []
    for page in paginator.paginate():
        elbv2s.extend(page["LoadBalancers"])

    # Make extra calls to get listeners
    for elbv2 in elbv2s:
        elbv2["Listeners"] = get_load_balancer_v2_listeners(
            client,
            elbv2["LoadBalancerArn"],
        )
        elbv2["TargetGroups"] = get_load_balancer_v2_target_groups(
            client,
            elbv2["LoadBalancerArn"],
        )
    return elbv2s


def _transform_load_balancer_v2_data(
    data: List[Dict],
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Transform load balancer v2 data, extracting relationships into separate lists.

    Returns a tuple of:
    - Load balancer data list (includes SecurityGroupIds and SubnetIds for one_to_many)
    - Listener data list
    - Target relationship data list (with target type info)
    """
    lb_data = []
    listener_data = []
    target_data = []

    for lb in data:
        dns_name = lb.get("DNSName")
        if not dns_name:
            logger.warning("Skipping load balancer entry with missing DNSName: %r", lb)
            continue

        # Extract subnet IDs for one_to_many relationship
        subnet_ids = [
            az["SubnetId"]
            for az in lb.get("AvailabilityZones", [])
            if az.get("SubnetId")
        ]

        # Transform load balancer data with SecurityGroupIds and SubnetIds for one_to_many
        lb_data.append(
            {
                "DNSName": dns_name,
                "LoadBalancerName": lb["LoadBalancerName"],
                "CanonicalHostedZoneId": lb.get("CanonicalHostedZoneNameID")
                or lb.get("CanonicalHostedZoneId"),
                "Type": lb.get("Type"),
                "Scheme": lb.get("Scheme"),
                "LoadBalancerArn": lb.get("LoadBalancerArn"),
                "CreatedTime": str(lb["CreatedTime"]),
                # Security groups as list for one_to_many relationship
                "SecurityGroupIds": lb.get("SecurityGroups", []),
                # Subnets as list for one_to_many relationship
                "SubnetIds": subnet_ids,
            }
        )

        # Extract listener data
        for listener in lb.get("Listeners", []):
            listener_data.append(
                {
                    "ListenerArn": listener["ListenerArn"],
                    "Port": listener.get("Port"),
                    "Protocol": listener.get("Protocol"),
                    "SslPolicy": listener.get("SslPolicy"),
                    "TargetGroupArn": listener.get("TargetGroupArn"),
                    "LoadBalancerId": dns_name,
                }
            )

        # Extract target relationships
        for target_group in lb.get("TargetGroups", []):
            target_type = target_group.get("TargetType")
            for target_id in target_group.get("Targets", []):
                target_data.append(
                    {
                        "LoadBalancerId": dns_name,
                        "TargetId": target_id,
                        "TargetType": target_type,
                        "TargetGroupArn": target_group.get("TargetGroupArn"),
                        "Port": target_group.get("Port"),
                        "Protocol": target_group.get("Protocol"),
                    }
                )

    return lb_data, listener_data, target_data


@timeit
def load_load_balancer_v2s(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    # Transform data
    lb_data, listener_data, target_data = _transform_load_balancer_v2_data(data)

    # Load main load balancer nodes (includes security group and subnet relationships via schema)
    load(
        neo4j_session,
        LoadBalancerV2Schema(),
        lb_data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )

    # Load listener nodes
    if listener_data:
        load(
            neo4j_session,
            ELBV2ListenerSchema(),
            listener_data,
            lastupdated=update_tag,
            AWS_ID=current_aws_account_id,
        )

    # Load target relationships
    if target_data:
        _load_load_balancer_v2_targets(
            neo4j_session,
            target_data,
            current_aws_account_id,
            update_tag,
        )


def _load_load_balancer_v2_targets(
    neo4j_session: neo4j.Session,
    target_data: List[Dict],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """Load EXPOSE relationships to various target types using MatchLinks."""
    # Group targets by type
    instance_targets = [t for t in target_data if t["TargetType"] == "instance"]
    ip_targets = [t for t in target_data if t["TargetType"] == "ip"]
    lambda_targets = [t for t in target_data if t["TargetType"] == "lambda"]
    alb_targets = [t for t in target_data if t["TargetType"] == "alb"]

    if instance_targets:
        load_matchlinks(
            neo4j_session,
            LoadBalancerV2ToEC2InstanceMatchLink(),
            instance_targets,
            lastupdated=update_tag,
            _sub_resource_label="AWSAccount",
            _sub_resource_id=current_aws_account_id,
        )

    if ip_targets:
        load_matchlinks(
            neo4j_session,
            LoadBalancerV2ToEC2PrivateIpMatchLink(),
            ip_targets,
            lastupdated=update_tag,
            _sub_resource_label="AWSAccount",
            _sub_resource_id=current_aws_account_id,
        )

    if lambda_targets:
        load_matchlinks(
            neo4j_session,
            LoadBalancerV2ToAWSLambdaMatchLink(),
            lambda_targets,
            lastupdated=update_tag,
            _sub_resource_label="AWSAccount",
            _sub_resource_id=current_aws_account_id,
        )

    if alb_targets:
        load_matchlinks(
            neo4j_session,
            LoadBalancerV2ToLoadBalancerV2MatchLink(),
            alb_targets,
            lastupdated=update_tag,
            _sub_resource_label="AWSAccount",
            _sub_resource_id=current_aws_account_id,
        )


@timeit
def load_load_balancer_v2_listeners(
    neo4j_session: neo4j.Session,
    load_balancer_id: str,
    listener_data: List[Dict],
    update_tag: int,
    aws_account_id: str,
) -> None:
    """Load ELBV2Listener nodes and their relationships to LoadBalancerV2."""
    # Transform listener data to include the load balancer id
    transformed_data = [
        {
            "ListenerArn": listener["ListenerArn"],
            "Port": listener.get("Port"),
            "Protocol": listener.get("Protocol"),
            "SslPolicy": listener.get("SslPolicy"),
            "TargetGroupArn": listener.get("TargetGroupArn"),
            "LoadBalancerId": load_balancer_id,
        }
        for listener in listener_data
    ]
    load(
        neo4j_session,
        ELBV2ListenerSchema(),
        transformed_data,
        lastupdated=update_tag,
        AWS_ID=aws_account_id,
    )


@timeit
def load_load_balancer_v2_target_groups(
    neo4j_session: neo4j.Session,
    load_balancer_id: str,
    target_groups: List[Dict],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """Load EXPOSE relationships from LoadBalancerV2 to target resources."""
    # Transform target groups to target data
    target_data = []
    for target_group in target_groups:
        target_type = target_group.get("TargetType")
        for target_id in target_group.get("Targets", []):
            target_data.append(
                {
                    "LoadBalancerId": load_balancer_id,
                    "TargetId": target_id,
                    "TargetType": target_type,
                    "TargetGroupArn": target_group.get("TargetGroupArn"),
                    "Port": target_group.get("Port"),
                    "Protocol": target_group.get("Protocol"),
                }
            )
    if target_data:
        _load_load_balancer_v2_targets(
            neo4j_session,
            target_data,
            current_aws_account_id,
            update_tag,
        )


@timeit
def cleanup_load_balancer_v2s(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """Delete elbv2's and dependent resources in the DB without the most recent
    lastupdated tag."""
    # Cleanup target MatchLinks first (relationships must be cleaned before nodes)
    for matchlink in [
        LoadBalancerV2ToEC2InstanceMatchLink(),
        LoadBalancerV2ToEC2PrivateIpMatchLink(),
        LoadBalancerV2ToAWSLambdaMatchLink(),
        LoadBalancerV2ToLoadBalancerV2MatchLink(),
    ]:
        GraphJob.from_matchlink(
            matchlink,
            "AWSAccount",
            common_job_parameters["AWS_ID"],
            common_job_parameters["UPDATE_TAG"],
        ).run(neo4j_session)

    # Cleanup LoadBalancerV2 nodes
    GraphJob.from_node_schema(
        LoadBalancerV2Schema(),
        common_job_parameters,
    ).run(neo4j_session)

    # Cleanup ELBV2Listener nodes
    GraphJob.from_node_schema(
        ELBV2ListenerSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_load_balancer_v2s(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    for region in regions:
        logger.info(
            "Syncing EC2 load balancers v2 for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        data = get_loadbalancer_v2_data(boto3_session, region)
        load_load_balancer_v2s(
            neo4j_session,
            data,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup_load_balancer_v2s(neo4j_session, common_job_parameters)
