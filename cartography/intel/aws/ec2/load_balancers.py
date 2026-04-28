import logging

import boto3
import neo4j
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError
from botocore.exceptions import EndpointConnectionError
from botocore.exceptions import ReadTimeoutError

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.models.aws.ec2.load_balancer_listeners import ELBListenerSchema
from cartography.models.aws.ec2.load_balancers import LoadBalancerSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


class ELBTransientRegionFailure(Exception):
    pass


TRANSIENT_REGION_EXCEPTIONS = (
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)

RETRYABLE_ELB_ERROR_CODES = {
    "InternalError",
    "InternalFailure",
    "RequestTimeout",
    "RequestTimeoutException",
    "ServiceUnavailable",
    "Throttling",
    "ThrottlingException",
    "TooManyRequestsException",
}

RETRYABLE_ELB_HTTP_STATUS_CODES = {500, 502, 503, 504}


def _is_retryable_elb_client_error(error: ClientError) -> bool:
    error_code = error.response.get("Error", {}).get("Code")
    status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    return (
        error_code in RETRYABLE_ELB_ERROR_CODES
        or status_code in RETRYABLE_ELB_HTTP_STATUS_CODES
    )


# DEPRECATED: Remove this migration function when releasing v1
def _migrate_legacy_loadbalancer_labels(neo4j_session: neo4j.Session) -> None:
    """One-time migration: relabel LoadBalancer → AWSLoadBalancer."""
    check_query = """
    MATCH (:AWSAccount)-[:RESOURCE]->(n:LoadBalancer)
    WHERE NOT n:AWSLoadBalancer AND NOT n:LoadBalancerV2
    RETURN count(n) as legacy_count
    """
    result = neo4j_session.run(check_query)
    legacy_count = result.single()["legacy_count"]

    if legacy_count == 0:
        return

    logger.info(f"Migrating {legacy_count} legacy LoadBalancer nodes...")
    migration_query = """
    MATCH (:AWSAccount)-[:RESOURCE]->(n:LoadBalancer)
    WHERE NOT n:AWSLoadBalancer AND NOT n:LoadBalancerV2
    SET n:AWSLoadBalancer
    RETURN count(n) as migrated
    """
    result = neo4j_session.run(migration_query)
    logger.info(f"Migrated {result.single()['migrated']} nodes")


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
    client = create_boto3_client(
        boto3_session, "elb", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("describe_load_balancers")
    elbs: list[dict] = []
    try:
        for page in paginator.paginate():
            elbs.extend(page["LoadBalancerDescriptions"])
    except TRANSIENT_REGION_EXCEPTIONS as error:
        raise ELBTransientRegionFailure(
            "Encountered a transient regional ELB endpoint failure while calling DescribeLoadBalancers"
        ) from error
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
    _migrate_legacy_loadbalancer_labels(neo4j_session)
    cleanup_safe = True

    for region in regions:
        logger.info(
            "Syncing EC2 load balancers for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        try:
            data = get_loadbalancer_data(boto3_session, region)
        except ELBTransientRegionFailure as error:
            cleanup_safe = False
            logger.warning(
                "Skipping classic ELB sync for account %s in region %s after transient ELB failure: %s",
                current_aws_account_id,
                region,
                error,
            )
            continue
        except ClientError as error:
            if _is_retryable_elb_client_error(error):
                cleanup_safe = False
                logger.warning(
                    "Skipping classic ELB sync for account %s in region %s after AWS client retries were exhausted: %s",
                    current_aws_account_id,
                    region,
                    error,
                )
                continue
            raise
        transformed_data, listener_data = transform_load_balancer_data(data)

        load_load_balancers(
            neo4j_session, transformed_data, region, current_aws_account_id, update_tag
        )
        load_load_balancer_listeners(
            neo4j_session, listener_data, region, current_aws_account_id, update_tag
        )

    if cleanup_safe:
        cleanup_load_balancers(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping classic ELB cleanup for account %s because one or more regions had transient ELB failures. Preserving last-known-good ELB state.",
            current_aws_account_id,
        )
