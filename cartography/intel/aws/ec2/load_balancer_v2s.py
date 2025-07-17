import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import botocore
import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.loadbalancerv2 import ELBV2ListenerSchema
from cartography.models.aws.ec2.loadbalancerv2 import (
    LoadBalancerV2ExposeInstanceMatchLink,
)
from cartography.models.aws.ec2.loadbalancerv2 import LoadBalancerV2Schema
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_load_balancer_v2_listeners(
    client: botocore.client.BaseClient,
    load_balancer_arn: str,
) -> list[dict[str, Any]]:
    paginator = client.get_paginator("describe_listeners")
    listeners: list[dict[str, Any]] = []
    for page in paginator.paginate(LoadBalancerArn=load_balancer_arn):
        listeners.extend(page["Listeners"])

    for listener in listeners:
        if "TargetGroupArn" not in listener:
            actions = listener.get("DefaultActions", [])
            if actions and actions[0].get("TargetGroupArn"):
                listener["TargetGroupArn"] = actions[0]["TargetGroupArn"]
    return listeners


@timeit
def get_load_balancer_v2_target_groups(
    client: botocore.client.BaseClient,
    load_balancer_arn: str,
) -> list[dict[str, Any]]:
    paginator = client.get_paginator("describe_target_groups")
    target_groups: list[dict[str, Any]] = []
    for page in paginator.paginate(LoadBalancerArn=load_balancer_arn):
        target_groups.extend(page["TargetGroups"])

    for target_group in target_groups:
        target_group["Targets"] = []
        target_health = client.describe_target_health(
            TargetGroupArn=target_group["TargetGroupArn"],
        )
        for th in target_health["TargetHealthDescriptions"]:
            target_group["Targets"].append(th["Target"]["Id"])
    return target_groups


@timeit
@aws_handle_regions
def get_loadbalancer_v2_data(
    boto3_session: boto3.Session, region: str
) -> list[dict[str, Any]]:
    client = boto3_session.client(
        "elbv2",
        region_name=region,
        config=get_botocore_config(),
    )
    paginator = client.get_paginator("describe_load_balancers")
    elbv2s: list[dict[str, Any]] = []
    for page in paginator.paginate():
        elbv2s.extend(page["LoadBalancers"])

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


def transform_load_balancer_v2s(
    load_balancers: list[dict[str, Any]], region: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    lbs: list[dict[str, Any]] = []
    listeners: list[dict[str, Any]] = []
    exposes: list[dict[str, Any]] = []
    for lb in load_balancers:
        lb_id = lb.get("DNSName")
        if not lb_id:
            logger.warning("Skipping load balancer entry with missing DNSName: %r", lb)
            continue
        item: dict[str, Any] = {
            "DNSName": lb_id,
            "LoadBalancerName": lb.get("LoadBalancerName"),
            "CanonicalHostedZoneNameID": lb.get("CanonicalHostedZoneNameID"),
            "Type": lb.get("Type"),
            "Scheme": lb.get("Scheme"),
            "CreatedTime": lb.get("CreatedTime"),
            "SubnetIds": [az["SubnetId"] for az in lb.get("AvailabilityZones", [])],
            "SecurityGroups": lb.get("SecurityGroups", []),
            "Region": region,
        }
        lbs.append(item)

        for listener in lb.get("Listeners", []):
            listeners.append(
                {
                    "ListenerArn": listener["ListenerArn"],
                    "Port": listener.get("Port"),
                    "Protocol": listener.get("Protocol"),
                    "SslPolicy": listener.get("SslPolicy"),
                    "TargetGroupArn": listener.get("TargetGroupArn"),
                    "LoadBalancerId": lb_id,
                    "Region": region,
                }
            )

        for tg in lb.get("TargetGroups", []):
            if tg.get("TargetType") != "instance":
                continue
            for instance in tg.get("Targets", []):
                exposes.append(
                    {
                        "ElbV2Id": lb_id,
                        "InstanceId": instance,
                        "Port": tg.get("Port"),
                        "Protocol": tg.get("Protocol"),
                        "TargetGroupArn": tg.get("TargetGroupArn"),
                    }
                )
    return lbs, listeners, exposes


@timeit
def load_load_balancer_v2s(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        LoadBalancerV2Schema(),
        data,
        lastupdated=update_tag,
        AWS_ID=current_aws_account_id,
        Region=region,
    )


@timeit
def load_elbv2_listeners(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ELBV2ListenerSchema(),
        data,
        lastupdated=update_tag,
        AWS_ID=current_aws_account_id,
        Region=region,
    )


@timeit
def load_elbv2_exposes(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load_matchlinks(
        neo4j_session,
        LoadBalancerV2ExposeInstanceMatchLink(),
        data,
        lastupdated=update_tag,
        _sub_resource_label="AWSAccount",
        _sub_resource_id=current_aws_account_id,
    )


@timeit
def cleanup_load_balancer_v2s(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    GraphJob.from_node_schema(LoadBalancerV2Schema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(ELBV2ListenerSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_matchlink(
        LoadBalancerV2ExposeInstanceMatchLink(),
        "AWSAccount",
        common_job_parameters["AWS_ID"],
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)


@timeit
def sync_load_balancer_v2s(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing EC2 load balancers v2 for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        raw = get_loadbalancer_v2_data(boto3_session, region)
        lbs, listeners, exposes = transform_load_balancer_v2s(raw, region)
        load_load_balancer_v2s(
            neo4j_session,
            lbs,
            region,
            current_aws_account_id,
            update_tag,
        )
        load_elbv2_listeners(
            neo4j_session,
            listeners,
            region,
            current_aws_account_id,
            update_tag,
        )
        load_elbv2_exposes(
            neo4j_session,
            exposes,
            current_aws_account_id,
            update_tag,
        )
    cleanup_load_balancer_v2s(neo4j_session, common_job_parameters)
