import json
import logging
from typing import Any

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.models.aws.ec2.vpc_endpoint import AWSVpcEndpointSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

from .util import get_botocore_config

logger = logging.getLogger(__name__)


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
        logger.warning(
            "Could not retrieve VPC Endpoints due to boto3 error %s: %s. Skipping.",
            e.response["Error"]["Code"],
            e.response["Error"]["Message"],
        )
    return vpc_endpoints


def transform_vpc_endpoint_data(
    vpc_endpoint_list: list[dict[str, Any]], region: str
) -> list[dict[str, Any]]:
    vpc_endpoint_data: list[dict[str, Any]] = []

    for endpoint in vpc_endpoint_list:
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
            "VpcEndpointId": endpoint.get("VpcEndpointId"),
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

    return vpc_endpoint_data


@timeit
def load_vpc_endpoints(
    neo4j_session: neo4j.Session,
    vpc_endpoints: list[dict[str, Any]],
    region: str,
    aws_account_id: str,
    update_tag: int,
) -> None:
    logger.info(f"Loading {len(vpc_endpoints)} VPC Endpoints for region '{region}' into graph.")
    load(
        neo4j_session,
        AWSVpcEndpointSchema(),
        vpc_endpoints,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=aws_account_id,
    )


@timeit
def load_vpc_endpoint_subnet_relationships(
    neo4j_session: neo4j.Session,
    vpc_endpoints: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Create relationships between VPC endpoints and subnets (for Interface and GatewayLoadBalancer endpoints)

    NOTE: Uses MERGE for subnet nodes to create stub nodes if subnets haven't been synced yet.
    This removes sync order dependency. The subnet sync will fill in full details later.
    """
    ingest_query = """
    UNWIND $Endpoints as endpoint
    MATCH (vpce:AWSVpcEndpoint {id: endpoint.VpcEndpointId})
    WITH vpce, endpoint
    UNWIND endpoint.SubnetIds as subnet_id
    MERGE (subnet:EC2Subnet {subnetid: subnet_id})
    ON CREATE SET subnet.firstseen = timestamp()
    SET subnet.lastupdated = $update_tag
    WITH vpce, subnet
    MERGE (vpce)-[r:USES_SUBNET]->(subnet)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    # Filter to only endpoints with subnets
    endpoints_with_subnets = [
        {"VpcEndpointId": ep["VpcEndpointId"], "SubnetIds": ep.get("SubnetIds", [])}
        for ep in vpc_endpoints
        if ep.get("SubnetIds")
    ]

    if endpoints_with_subnets:
        run_write_query(
            neo4j_session,
            ingest_query,
            Endpoints=endpoints_with_subnets,
            update_tag=update_tag,
        )


@timeit
def load_vpc_endpoint_security_group_relationships(
    neo4j_session: neo4j.Session,
    vpc_endpoints: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Create relationships between VPC endpoints and security groups (for Interface and GatewayLoadBalancer endpoints)

    NOTE: Uses MERGE for security group nodes to create stub nodes if security groups haven't been synced yet.
    This removes sync order dependency. The security group sync will fill in full details later.
    """
    ingest_query = """
    UNWIND $Endpoints as endpoint
    MATCH (vpce:AWSVpcEndpoint {id: endpoint.VpcEndpointId})
    WITH vpce, endpoint
    UNWIND endpoint.Groups as group
    MERGE (sg:EC2SecurityGroup {id: group.GroupId})
    ON CREATE SET sg.firstseen = timestamp()
    SET sg.lastupdated = $update_tag
    WITH vpce, sg
    MERGE (vpce)-[r:MEMBER_OF_SECURITY_GROUP]->(sg)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    # Filter to only endpoints with security groups
    endpoints_with_groups = [
        {"VpcEndpointId": ep["VpcEndpointId"], "Groups": ep.get("Groups", [])}
        for ep in vpc_endpoints
        if ep.get("Groups")
    ]

    if endpoints_with_groups:
        run_write_query(
            neo4j_session,
            ingest_query,
            Endpoints=endpoints_with_groups,
            update_tag=update_tag,
        )


@timeit
def load_vpc_endpoint_route_table_relationships(
    neo4j_session: neo4j.Session,
    vpc_endpoints: list[dict[str, Any]],
    update_tag: int,
) -> None:
    """
    Create relationships between VPC endpoints and route tables (for Gateway endpoints)

    NOTE: Uses MERGE for route table nodes to create stub nodes if route tables haven't been synced yet.
    This removes sync order dependency. The route table sync will fill in full details later.
    """
    ingest_query = """
    UNWIND $Endpoints as endpoint
    MATCH (vpce:AWSVpcEndpoint {id: endpoint.VpcEndpointId})
    WITH vpce, endpoint
    UNWIND endpoint.RouteTableIds as route_table_id
    MERGE (rtb:AWSRouteTable {id: route_table_id})
    ON CREATE SET rtb.firstseen = timestamp()
    SET rtb.lastupdated = $update_tag
    WITH vpce, rtb
    MERGE (vpce)-[r:ROUTES_THROUGH]->(rtb)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """

    # Filter to only endpoints with route tables
    endpoints_with_route_tables = [
        {"VpcEndpointId": ep["VpcEndpointId"], "RouteTableIds": ep.get("RouteTableIds", [])}
        for ep in vpc_endpoints
        if ep.get("RouteTableIds")
    ]

    if endpoints_with_route_tables:
        run_write_query(
            neo4j_session,
            ingest_query,
            Endpoints=endpoints_with_route_tables,
            update_tag=update_tag,
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    # Clean up manually created relationships that aren't part of the schema
    cleanup_manual_relationships_query = """
    MATCH (vpce:AWSVpcEndpoint)<-[:RESOURCE]-(:AWSAccount{id: $AWS_ID})
    OPTIONAL MATCH (vpce)-[r1:USES_SUBNET]->(:EC2Subnet)
    WHERE r1.lastupdated <> $UPDATE_TAG
    OPTIONAL MATCH (vpce)-[r2:MEMBER_OF_SECURITY_GROUP]->(:EC2SecurityGroup)
    WHERE r2.lastupdated <> $UPDATE_TAG
    OPTIONAL MATCH (vpce)-[r3:ROUTES_THROUGH]->(:AWSRouteTable)
    WHERE r3.lastupdated <> $UPDATE_TAG
    WITH collect(r1) + collect(r2) + collect(r3) as stale_rels
    UNWIND stale_rels as r
    DELETE r
    """
    run_write_query(
        neo4j_session,
        cleanup_manual_relationships_query,
        AWS_ID=common_job_parameters["AWS_ID"],
        UPDATE_TAG=common_job_parameters["UPDATE_TAG"],
    )

    # Clean up schema-based nodes and relationships
    GraphJob.from_node_schema(AWSVpcEndpointSchema(), common_job_parameters).run(
        neo4j_session
    )


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
        vpc_endpoint_data = transform_vpc_endpoint_data(raw_vpc_endpoint_data, region)
        load_vpc_endpoints(
            neo4j_session,
            vpc_endpoint_data,
            region,
            current_aws_account_id,
            update_tag,
        )
        load_vpc_endpoint_subnet_relationships(
            neo4j_session,
            vpc_endpoint_data,
            update_tag,
        )
        load_vpc_endpoint_security_group_relationships(
            neo4j_session,
            vpc_endpoint_data,
            update_tag,
        )
        load_vpc_endpoint_route_table_relationships(
            neo4j_session,
            vpc_endpoint_data,
            update_tag,
        )
    cleanup(neo4j_session, common_job_parameters)
