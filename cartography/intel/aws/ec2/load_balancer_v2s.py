import logging
from typing import Dict
from typing import List
from typing import Tuple

import boto3
import botocore
import neo4j
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import EndpointConnectionError
from botocore.exceptions import ReadTimeoutError

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.models.aws.ec2.loadbalancerv2 import ELBV2ListenerSchema
from cartography.models.aws.ec2.loadbalancerv2 import ELBV2TargetGroupSchema
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

logger = logging.getLogger(__name__)


class ELBV2TransientRegionFailure(Exception):
    pass


TRANSIENT_REGION_EXCEPTIONS = (
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)

RETRYABLE_ELBV2_ERROR_CODES = {
    "InternalError",
    "InternalFailure",
    "RequestTimeout",
    "RequestTimeoutException",
    "ServiceUnavailable",
    "Throttling",
    "ThrottlingException",
    "TooManyRequestsException",
}

RETRYABLE_ELBV2_HTTP_STATUS_CODES = {500, 502, 503, 504}


def _is_retryable_elbv2_client_error(error: ClientError) -> bool:
    error_code = error.response.get("Error", {}).get("Code")
    status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    return (
        error_code in RETRYABLE_ELBV2_ERROR_CODES
        or status_code in RETRYABLE_ELBV2_HTTP_STATUS_CODES
    )


# DEPRECATED: Remove this migration function when releasing v1
def _migrate_legacy_loadbalancerv2_labels(neo4j_session: neo4j.Session) -> None:
    """One-time migration: relabel LoadBalancerV2 → AWSLoadBalancerV2."""
    check_query = """
    MATCH (:AWSAccount)-[:RESOURCE]->(n:LoadBalancerV2)
    WHERE NOT n:AWSLoadBalancerV2 AND NOT n:LoadBalancer
    RETURN count(n) as legacy_count
    """
    result = neo4j_session.run(check_query)
    legacy_count = result.single()["legacy_count"]

    if legacy_count == 0:
        return

    logger.info(f"Migrating {legacy_count} legacy LoadBalancerV2 nodes...")
    migration_query = """
    MATCH (:AWSAccount)-[:RESOURCE]->(n:LoadBalancerV2)
    WHERE NOT n:AWSLoadBalancerV2 AND NOT n:LoadBalancer
    SET n:AWSLoadBalancerV2
    RETURN count(n) as migrated
    """
    result = neo4j_session.run(migration_query)
    logger.info(f"Migrated {result.single()['migrated']} nodes")


@timeit
@aws_handle_regions
def get_load_balancer_v2_listeners(
    client: botocore.client.BaseClient,
    load_balancer_arn: str,
) -> List[Dict]:
    paginator = client.get_paginator("describe_listeners")
    listeners: List[Dict] = []
    try:
        for page in paginator.paginate(LoadBalancerArn=load_balancer_arn):
            listeners.extend(page["Listeners"])
    except TRANSIENT_REGION_EXCEPTIONS as error:
        raise ELBV2TransientRegionFailure(
            f"Encountered a transient regional ELBV2 endpoint failure while calling DescribeListeners on load balancer {load_balancer_arn}"
        ) from error

    return listeners


@timeit
def get_load_balancer_v2_target_groups(
    client: botocore.client.BaseClient,
    load_balancer_arn: str,
) -> List[Dict]:
    paginator = client.get_paginator("describe_target_groups")
    target_groups: List[Dict] = []
    try:
        for page in paginator.paginate(LoadBalancerArn=load_balancer_arn):
            target_groups.extend(page["TargetGroups"])
    except TRANSIENT_REGION_EXCEPTIONS as error:
        raise ELBV2TransientRegionFailure(
            f"Encountered a transient regional ELBV2 endpoint failure while calling DescribeTargetGroups on load balancer {load_balancer_arn}"
        ) from error

    # Add instance data
    for target_group in target_groups:
        target_group["Targets"] = []
        try:
            target_health = client.describe_target_health(
                TargetGroupArn=target_group["TargetGroupArn"],
            )
        except TRANSIENT_REGION_EXCEPTIONS as error:
            raise ELBV2TransientRegionFailure(
                f"Encountered a transient regional ELBV2 endpoint failure while calling DescribeTargetHealth on target group {target_group['TargetGroupArn']}"
            ) from error
        for target_health_description in target_health["TargetHealthDescriptions"]:
            target_group["Targets"].append(target_health_description["Target"]["Id"])

    return target_groups


@timeit
@aws_handle_regions
def get_loadbalancer_v2_data(boto3_session: boto3.Session, region: str) -> List[Dict]:
    client = create_boto3_client(
        boto3_session,
        "elbv2",
        region_name=region,
        config=get_botocore_config(),
    )
    paginator = client.get_paginator("describe_load_balancers")
    elbv2s: List[Dict] = []
    try:
        for page in paginator.paginate():
            elbv2s.extend(page["LoadBalancers"])
    except TRANSIENT_REGION_EXCEPTIONS as error:
        raise ELBV2TransientRegionFailure(
            "Encountered a transient regional ELBV2 endpoint failure while calling DescribeLoadBalancers"
        ) from error

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
) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict]]:
    """
    Transform load balancer v2 data, extracting relationships into separate lists.

    Returns a tuple of:
    - Load balancer data list (includes SecurityGroupIds and SubnetIds for one_to_many)
    - Listener data list
    - Target group node data list (one per distinct TargetGroupArn)
    - Target relationship data list (with target type info)
    """
    lb_data = []
    listener_data = []
    target_data = []
    tg_by_arn: dict[str, dict] = {}

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

        # Extract target group nodes and target relationships
        for target_group in lb.get("TargetGroups", []):
            tg_arn = target_group["TargetGroupArn"]
            if tg_arn in tg_by_arn:
                tg_by_arn[tg_arn]["LoadBalancerId"].append(dns_name)
            else:
                tg_by_arn[tg_arn] = {
                    "TargetGroupArn": tg_arn,
                    "TargetGroupName": target_group.get("TargetGroupName"),
                    "TargetType": target_group.get("TargetType"),
                    "Protocol": target_group.get("Protocol"),
                    "Port": target_group.get("Port"),
                    "VpcId": target_group.get("VpcId"),
                    "LoadBalancerId": [dns_name],
                }

            target_type = target_group.get("TargetType")
            for target_id in target_group.get("Targets", []):
                target_data.append(
                    {
                        "LoadBalancerId": dns_name,
                        "TargetId": target_id,
                        "TargetType": target_type,
                        "TargetGroupArn": tg_arn,
                        "Port": target_group.get("Port"),
                        "Protocol": target_group.get("Protocol"),
                    }
                )

    return lb_data, listener_data, list(tg_by_arn.values()), target_data


@timeit
def load_load_balancer_v2s(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    # Transform data
    lb_data, listener_data, tg_node_data, target_data = (
        _transform_load_balancer_v2_data(data)
    )

    # Load main load balancer nodes (includes security group and subnet relationships via schema)
    load(
        neo4j_session,
        LoadBalancerV2Schema(),
        lb_data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )

    # Load target group nodes
    if tg_node_data:
        load(
            neo4j_session,
            ELBV2TargetGroupSchema(),
            tg_node_data,
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

    # Load non-IP target relationships (instance, lambda, alb)
    # IP targets are deferred to sync_load_balancer_v2_expose so that EC2PrivateIp nodes
    # created by ec2:network_interface exist first.
    if target_data:
        _load_load_balancer_v2_non_ip_targets(
            neo4j_session,
            target_data,
            current_aws_account_id,
            update_tag,
        )


def _load_load_balancer_v2_non_ip_targets(
    neo4j_session: neo4j.Session,
    target_data: List[Dict],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """Load EXPOSE relationships to non-IP target types (instance, lambda, alb) using MatchLinks."""
    instance_targets = [t for t in target_data if t["TargetType"] == "instance"]
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


def _load_load_balancer_v2_ip_targets(
    neo4j_session: neo4j.Session,
    target_data: List[Dict],
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    """Load EXPOSE relationships to IP target types (EC2PrivateIp) using MatchLinks."""
    ip_targets = [t for t in target_data if t["TargetType"] == "ip"]

    if ip_targets:
        load_matchlinks(
            neo4j_session,
            LoadBalancerV2ToEC2PrivateIpMatchLink(),
            ip_targets,
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
    region: str | None = None,
) -> None:
    """Load ELBV2TargetGroup nodes and EXPOSE relationships from LoadBalancerV2 to target resources."""
    # Load target group nodes
    tg_node_data = []
    for tg in target_groups:
        tg_node_data.append(
            {
                "TargetGroupArn": tg["TargetGroupArn"],
                "TargetGroupName": tg.get("TargetGroupName"),
                "TargetType": tg.get("TargetType"),
                "Protocol": tg.get("Protocol"),
                "Port": tg.get("Port"),
                "VpcId": tg.get("VpcId"),
                "LoadBalancerId": [load_balancer_id],
            }
        )
    if tg_node_data:
        load(
            neo4j_session,
            ELBV2TargetGroupSchema(),
            tg_node_data,
            lastupdated=update_tag,
            Region=region,
            AWS_ID=current_aws_account_id,
        )

    # Transform target groups to target data for EXPOSE relationships
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
        _load_load_balancer_v2_non_ip_targets(
            neo4j_session,
            target_data,
            current_aws_account_id,
            update_tag,
        )
        _load_load_balancer_v2_ip_targets(
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
    lastupdated tag. Cleans up non-IP MatchLinks, nodes, and listeners."""
    # Cleanup non-IP target MatchLinks first (relationships must be cleaned before nodes)
    for matchlink in [
        LoadBalancerV2ToEC2InstanceMatchLink(),
        LoadBalancerV2ToAWSLambdaMatchLink(),
        LoadBalancerV2ToLoadBalancerV2MatchLink(),
    ]:
        GraphJob.from_matchlink(
            matchlink,
            "AWSAccount",
            common_job_parameters["AWS_ID"],
            common_job_parameters["UPDATE_TAG"],
        ).run(neo4j_session)

    # Cleanup ELBV2TargetGroup nodes before LoadBalancerV2 so ELBV2_TARGET_GROUP rels detach first
    GraphJob.from_node_schema(
        ELBV2TargetGroupSchema(),
        common_job_parameters,
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
def cleanup_load_balancer_v2_expose(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """Cleanup stale IP target MatchLinks (EC2PrivateIp EXPOSE relationships)."""
    GraphJob.from_matchlink(
        LoadBalancerV2ToEC2PrivateIpMatchLink(),
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
    common_job_parameters: Dict,
) -> None:
    """Phase 1: Sync LBv2 nodes, listeners, and non-IP MatchLinks (instance, lambda, alb).

    IP target MatchLinks are deferred to sync_load_balancer_v2_expose (Phase 2)
    so that EC2PrivateIp nodes created by ec2:network_interface exist first.
    """
    _migrate_legacy_loadbalancerv2_labels(neo4j_session)
    cleanup_safe = True

    for region in regions:
        logger.info(
            "Syncing EC2 load balancers v2 for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        try:
            data = get_loadbalancer_v2_data(boto3_session, region)
        except ELBV2TransientRegionFailure as error:
            cleanup_safe = False
            logger.warning(
                "Skipping ELBV2 sync for account %s in region %s after transient ELBV2 failure: %s",
                current_aws_account_id,
                region,
                error,
            )
            continue
        except ClientError as error:
            if _is_retryable_elbv2_client_error(error):
                cleanup_safe = False
                logger.warning(
                    "Skipping ELBV2 sync for account %s in region %s after AWS client retries were exhausted: %s",
                    current_aws_account_id,
                    region,
                    error,
                )
                continue
            raise
        load_load_balancer_v2s(
            neo4j_session,
            data,
            region,
            current_aws_account_id,
            update_tag,
        )
    if cleanup_safe:
        cleanup_load_balancer_v2s(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping ELBV2 cleanup for account %s because one or more regions had transient ELBV2 failures. Preserving last-known-good ELBV2 state.",
            current_aws_account_id,
        )


@timeit
def sync_load_balancer_v2_expose(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    """Phase 2: Sync IP target MatchLinks (LBv2 -> EC2PrivateIp EXPOSE relationships).

    Runs after ec2:network_interface so that EC2PrivateIp nodes exist.
    Re-fetches LBv2 data from AWS API to get target information.
    """
    cleanup_safe = True
    for region in regions:
        logger.info(
            "Syncing EC2 load balancer v2 IP targets for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        try:
            data = get_loadbalancer_v2_data(boto3_session, region)
        except ELBV2TransientRegionFailure as error:
            cleanup_safe = False
            logger.warning(
                "Skipping ELBV2 IP target sync for account %s in region %s after transient ELBV2 failure: %s",
                current_aws_account_id,
                region,
                error,
            )
            continue
        except ClientError as error:
            if _is_retryable_elbv2_client_error(error):
                cleanup_safe = False
                logger.warning(
                    "Skipping ELBV2 IP target sync for account %s in region %s after AWS client retries were exhausted: %s",
                    current_aws_account_id,
                    region,
                    error,
                )
                continue
            raise
        _, _, _, target_data = _transform_load_balancer_v2_data(data)
        _load_load_balancer_v2_ip_targets(
            neo4j_session,
            target_data,
            current_aws_account_id,
            update_tag,
        )
    if cleanup_safe:
        cleanup_load_balancer_v2_expose(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping ELBV2 IP target cleanup for account %s because one or more regions had transient ELBV2 failures. Preserving last-known-good ELBV2 IP target state.",
            current_aws_account_id,
        )
