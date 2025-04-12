import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.ec2.route_table_associations import RouteTableAssociationSchema
from cartography.models.aws.ec2.route_tables import RouteTableSchema
from cartography.models.aws.ec2.routes import RouteSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


def transform_route_table_associations(route_table_id: str, associations: List[Dict]) -> List[Dict]:
    """
    Transform route table association data into a format suitable for cartography ingestion.

    Args:
        route_table_id: The ID of the route table
        associations: List of association data from AWS API

    Returns:
        List of transformed association data
    """
    transformed = []
    for association in associations:
        transformed_association = {
            'id': association['RouteTableAssociationId'],
            'route_table_id': route_table_id,
            'subnet_id': association.get('SubnetId'),
            'gateway_id': association.get('GatewayId'),
            'main': association.get('Main', False),
        }
        transformed.append(transformed_association)
    return transformed


def transform_route_table_routes(route_table_id: str, routes: List[Dict]) -> List[Dict]:
    """
    Transform route table route data into a format suitable for cartography ingestion.

    Args:
        route_table_id: The ID of the route table
        routes: List of route data from AWS API

    Returns:
        List of transformed route data
    """
    transformed = []
    for route in routes:
        transformed_route = {
            'id': (
                f"{route_table_id}-{route.get('DestinationCidrBlock', '')}-{route.get('DestinationIpv6CidrBlock', '')}"
            ),
            'route_table_id': route_table_id,
            'destination_cidr_block': route.get('DestinationCidrBlock'),
            'destination_ipv6_cidr_block': route.get('DestinationIpv6CidrBlock'),
            'gateway_id': route.get('GatewayId'),
            'instance_id': route.get('InstanceId'),
            'instance_owner_id': route.get('InstanceOwnerId'),
            'nat_gateway_id': route.get('NatGatewayId'),
            'transit_gateway_id': route.get('TransitGatewayId'),
            'local_gateway_id': route.get('LocalGatewayId'),
            'carrier_gateway_id': route.get('CarrierGatewayId'),
            'network_interface_id': route.get('NetworkInterfaceId'),
            'vpc_peering_connection_id': route.get('VpcPeeringConnectionId'),
            'state': route.get('State'),
            'origin': route.get('Origin'),
        }
        transformed.append(transformed_route)
    return transformed


def transform_route_table_data(route_tables: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Transform route table data into a format suitable for cartography ingestion.

    Args:
        route_tables: List of route table data from AWS API

    Returns:
        Tuple of (transformed route table data, transformed association data, transformed route data)
    """
    transformed_tables = []
    association_data = []
    route_data = []

    for rt in route_tables:
        route_table_id = rt['RouteTableId']
        transformed_rt = {
            'id': route_table_id,
            'route_table_id': route_table_id,
            'owner_id': rt.get('OwnerId'),
            'vpc_id': rt.get('VpcId'),
            'VpnGatewayIds': [vgw['GatewayId'] for vgw in rt.get('PropagatingVgws', [])],
            'RouteTableAssociationIds': [assoc['RouteTableAssociationId'] for assoc in rt.get('Associations', [])],
            'RouteIds': [route['RouteId'] for route in rt.get('Routes', [])],
            'tags': rt.get('Tags', []),
        }
        transformed_tables.append(transformed_rt)

        # Transform associations
        if rt.get('Associations'):
            association_data.extend(transform_route_table_associations(route_table_id, rt['Associations']))

        # Transform routes
        if rt.get('Routes'):
            route_data.extend(transform_route_table_routes(route_table_id, rt['Routes']))

    return transformed_tables, association_data, route_data


@timeit
@aws_handle_regions
def get_route_tables(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    """
    Get route tables for a given region.
    """
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    paginator = client.get_paginator('describe_route_tables')
    route_tables: List[Dict[str, Any]] = []
    for page in paginator.paginate():
        route_tables.extend(page['RouteTables'])
    return route_tables


@timeit
def load_route_tables(
        neo4j_session: neo4j.Session,
        data: List[Dict],
        region: str,
        current_aws_account_id: str,
        update_tag: int,
) -> None:
    """
    Load route tables into Neo4j.
    """
    load(
        neo4j_session,
        RouteTableSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_route_table_associations(
        neo4j_session: neo4j.Session,
        data: List[Dict],
        region: str,
        current_aws_account_id: str,
        update_tag: int,
) -> None:
    """
    Load route table associations into Neo4j.
    """
    load(
        neo4j_session,
        RouteTableAssociationSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def load_routes(
        neo4j_session: neo4j.Session,
        data: List[Dict],
        region: str,
        current_aws_account_id: str,
        update_tag: int,
) -> None:
    """
    Load routes into Neo4j.
    """
    load(
        neo4j_session,
        RouteSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    """
    Clean up old route table data.
    """
    logger.debug("Running EC2 route tables cleanup")
    GraphJob.from_node_schema(RouteTableSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(RouteSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(RouteTableAssociationSchema(), common_job_parameters).run(neo4j_session)


@timeit
def sync_route_tables(
        neo4j_session: neo4j.Session,
        boto3_session: boto3.session.Session,
        regions: List[str],
        current_aws_account_id: str,
        update_tag: int,
        common_job_parameters: Dict[str, Any],
) -> None:
    """
    Sync route tables for all regions.
    """
    for region in regions:
        logger.info("Syncing EC2 route tables for region '%s' in account '%s'.", region, current_aws_account_id)
        route_tables = get_route_tables(boto3_session, region)
        transformed_tables, association_data, route_data = transform_route_table_data(route_tables)
        load_route_tables(neo4j_session, transformed_tables, region, current_aws_account_id, update_tag)
        load_route_table_associations(neo4j_session, association_data, region, current_aws_account_id, update_tag)
        load_routes(neo4j_session, route_data, region, current_aws_account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
