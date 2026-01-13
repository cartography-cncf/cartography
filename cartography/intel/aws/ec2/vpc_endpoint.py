import json
import logging
from collections import namedtuple
from typing import Any

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.routetable_vpc_endpoint import (
    AWSRouteTableVPCEndpointSchema,
)
from cartography.models.aws.ec2.securitygroup_vpc_endpoint import (
    EC2SecurityGroupVPCEndpointSchema,
)
from cartography.models.aws.ec2.subnet_vpc_endpoint import EC2SubnetVPCEndpointSchema
from cartography.models.aws.ec2.vpc_endpoint import AWSVpcEndpointSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)

VpcEndpointData = namedtuple(
    "VpcEndpointData",
    [
        "vpc_endpoint_list",
        "subnet_list",
        "security_group_list",
        "route_table_list",
    ],
)


@timeit
@aws_handle_regions
def get_vpc_endpoints(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    client = boto3_session.client(
        "ec2",
        region_name=region,
        config=get_botocore_config(),
    )
    vpc_endpoints: list[dict[str, Any]] = []
    try:
        paginator = client.get_paginator("describe_vpc_endpoints")
        for page in paginator.paginate():
            vpc_endpoints.extend(page.get("VpcEndpoints", []))
    except botocore.exceptions.ClientError as e:
        # Note: @aws_handle_regions decorator handles region-specific permission errors
        # by returning [] for opt-in or disabled regions. This is the established pattern.
        # For other errors (e.g., Throttling, ServiceUnavailable), log and skip.
        logger.warning(
            "Could not retrieve VPC Endpoints due to boto3 error %s: %s. Skipping.",
            e.response["Error"]["Code"],
            e.response["Error"]["Message"],
        )
    return vpc_endpoints


def transform_vpc_endpoint_data(
    vpc_endpoint_list: list[dict[str, Any]],
) -> VpcEndpointData:
    vpc_endpoint_data: list[dict[str, Any]] = []
    subnet_list: list[dict[str, Any]] = []
    security_group_list: list[dict[str, Any]] = []
    route_table_list: list[dict[str, Any]] = []

    for endpoint in vpc_endpoint_list:
        vpc_endpoint_id = endpoint.get("VpcEndpointId")

        # Convert policy document to string if present
        policy_doc = endpoint.get("PolicyDocument")
        if policy_doc:
            # Policy may already be a string or could be a dict
            if isinstance(policy_doc, dict):
                policy_doc = json.dumps(policy_doc)

        # Convert DNS entries to JSON string for storage
        dns_entries = endpoint.get("DnsEntries", [])
        dns_entries_str = json.dumps(dns_entries) if dns_entries else None

        # Convert creation timestamp to string
        creation_ts = endpoint.get("CreationTimestamp")
        if creation_ts:
            creation_ts = creation_ts.isoformat()

        endpoint_record = {
            "VpcEndpointId": vpc_endpoint_id,
            "VpcId": endpoint.get("VpcId"),
            "ServiceName": endpoint.get("ServiceName"),
            "ServiceRegion": endpoint.get("ServiceRegion"),
            "VpcEndpointType": endpoint.get("VpcEndpointType"),
            "State": endpoint.get("State"),
            "PolicyDocument": policy_doc,
            "RouteTableIds": endpoint.get("RouteTableIds", []),
            "SubnetIds": endpoint.get("SubnetIds", []),
            "NetworkInterfaceIds": endpoint.get("NetworkInterfaceIds", []),
            "DnsEntries": dns_entries_str,
            "PrivateDnsEnabled": endpoint.get("PrivateDnsEnabled"),
            "RequesterManaged": endpoint.get("RequesterManaged"),
            "IpAddressType": endpoint.get("IpAddressType"),
            "OwnerId": endpoint.get("OwnerId"),
            "CreationTimestamp": creation_ts,
            "Groups": endpoint.get("Groups", []),
            "lastupdated": endpoint.get("lastupdated"),
        }
        vpc_endpoint_data.append(endpoint_record)

        # Flatten subnets for Interface and GatewayLoadBalancer endpoints
        for subnet_id in endpoint.get("SubnetIds", []):
            subnet_list.append(
                {
                    "SubnetId": subnet_id,
                    "VpcEndpointId": vpc_endpoint_id,
                },
            )

        # Flatten security groups for Interface and GatewayLoadBalancer endpoints
        for group in endpoint.get("Groups", []):
            security_group_list.append(
                {
                    "GroupId": group.get("GroupId"),
                    "VpcEndpointId": vpc_endpoint_id,
                },
            )

        # Flatten route tables for Gateway endpoints
        for route_table_id in endpoint.get("RouteTableIds", []):
            route_table_list.append(
                {
                    "RouteTableId": route_table_id,
                    "VpcEndpointId": vpc_endpoint_id,
                },
            )

    return VpcEndpointData(
        vpc_endpoint_list=vpc_endpoint_data,
        subnet_list=subnet_list,
        security_group_list=security_group_list,
        route_table_list=route_table_list,
    )


@timeit
def load_vpc_endpoints(
    neo4j_session: neo4j.Session,
    vpc_endpoints: list[dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    logger.info(
        f"Loading {len(vpc_endpoints)} VPC Endpoints for region '{region}' into graph."
    )
    load(
        neo4j_session,
        AWSVpcEndpointSchema(),
        vpc_endpoints,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
    )


@timeit
def load_vpc_endpoint_subnets(
    neo4j_session: neo4j.Session,
    subnet_list: list[dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load subnet nodes and USES_SUBNET relationships from VPC endpoints.
    Uses schema-based loading for automatic cleanup handling.
    """
    if subnet_list:
        logger.info(f"Loading {len(subnet_list)} VPC endpoint subnet relationships.")
        load(
            neo4j_session,
            EC2SubnetVPCEndpointSchema(),
            subnet_list,
            lastupdated=update_tag,
            Region=region,
            AWS_ID=aws_account_id,
        )


@timeit
def load_vpc_endpoint_security_groups(
    neo4j_session: neo4j.Session,
    security_group_list: list[dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load security group nodes and MEMBER_OF_SECURITY_GROUP relationships from VPC endpoints.
    Uses schema-based loading for automatic cleanup handling.
    """
    if security_group_list:
        logger.info(
            f"Loading {len(security_group_list)} VPC endpoint security group relationships."
        )
        load(
            neo4j_session,
            EC2SecurityGroupVPCEndpointSchema(),
            security_group_list,
            lastupdated=update_tag,
            Region=region,
            AWS_ID=aws_account_id,
        )


@timeit
def load_vpc_endpoint_route_tables(
    neo4j_session: neo4j.Session,
    route_table_list: list[dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    """
    Load route table nodes and ROUTES_THROUGH relationships from Gateway VPC endpoints.
    Uses schema-based loading for automatic cleanup handling.
    """
    if route_table_list:
        logger.info(
            f"Loading {len(route_table_list)} VPC endpoint route table relationships."
        )
        load(
            neo4j_session,
            AWSRouteTableVPCEndpointSchema(),
            route_table_list,
            lastupdated=update_tag,
            Region=region,
            AWS_ID=aws_account_id,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    """
    Clean up stale VPC endpoint nodes and all related relationships.
    GraphJob.from_node_schema automatically handles cleanup for schema-defined relationships.
    """
    GraphJob.from_node_schema(AWSVpcEndpointSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(EC2SubnetVPCEndpointSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(
        EC2SecurityGroupVPCEndpointSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        AWSRouteTableVPCEndpointSchema(), common_job_parameters
    ).run(neo4j_session)


@timeit
def sync_vpc_endpoints(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing VPC Endpoints for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        raw_vpc_endpoint_data = get_vpc_endpoints(boto3_session, region)
        vpc_endpoint_data = transform_vpc_endpoint_data(raw_vpc_endpoint_data)
        load_vpc_endpoints(
            neo4j_session,
            vpc_endpoint_data.vpc_endpoint_list,
            region,
            current_aws_account_id,
            update_tag,
        )
        load_vpc_endpoint_subnets(
            neo4j_session,
            vpc_endpoint_data.subnet_list,
            region,
            current_aws_account_id,
            update_tag,
        )
        load_vpc_endpoint_security_groups(
            neo4j_session,
            vpc_endpoint_data.security_group_list,
            region,
            current_aws_account_id,
            update_tag,
        )
        load_vpc_endpoint_route_tables(
            neo4j_session,
            vpc_endpoint_data.route_table_list,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
