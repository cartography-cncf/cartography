import logging
import time
from typing import Dict
from typing import List

import boto3
import neo4j
from botocore.exceptions import ClientError
from cloudconsolelink.clouds.aws import AWSLinker

from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit
# from cartography.intel.aws.util.common import get_default_vpc

logger = logging.getLogger(__name__)
aws_console_link = AWSLinker()


def get_default_vpc(ec2_client):
    try:
        response = ec2_client.describe_vpcs(
            Filters=[{'Name': 'isDefault', 'Values': ['true']}],
        )
        vpcs = response.get('Vpcs', [])

        if not vpcs:
            logger.info("No default VPC found.")
            return {}

        return vpcs[0]

    except Exception as e:
        logger.error(f"Error fetching default VPC: {e}")
        return {}


@timeit
@aws_handle_regions
def get_route_tables_data(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client('ec2', region_name=region, config=get_botocore_config())
    try:
        paginator = client.get_paginator('describe_route_tables')
        route_tables: List[Dict] = []
        for page in paginator.paginate():
            route_tables.extend(page['RouteTables'])

        default_vpc = get_default_vpc(client)

        for route_table in route_tables:
            route_table['isDefault'] = False

            if default_vpc and route_table.get('VpcId') == default_vpc.get('VpcId'):
                associations = route_table.get('Associations', [])
                for association in associations:
                    if association.get('Main', False):
                        route_table['isDefault'] = True
                        break

            route_table['region'] = region

    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDeniedException' or e.response['Error']['Code'] == 'UnauthorizedOperation':
            logger.warning(
                'ec2:describe_subnets failed with AccessDeniedException; continuing sync.',
                exc_info=True,
            )

        else:
            raise

    return route_tables


@timeit
def load_route_tables(
    neo4j_session: neo4j.Session, data: List[Dict], aws_account_id: str,
    aws_update_tag: int,
) -> None:
    routes: List[Dict] = []
    associations: List[Dict] = []
    for route_table in data:
        route_table['arn'] = f"arn:aws:ec2:{route_table['region']}:{aws_account_id}:route-table/{route_table['RouteTableId']}"
        route_table['consolelink'] = aws_console_link.get_console_link(arn=route_table['arn'])
        associations.extend(route_table['Associations'])
        for route in route_table['Routes']:
            route['RouteTableId'] = route_table['RouteTableId']
            route['id'] = f"route_table/{route_table['RouteTableId']}/destination_cidr/{route.get('DestinationCidrBlock', route.get('DestinationIpv6CidrBlock'))}"
            routes.append(route)
    neo4j_session.execute_write(load_route_tables_tx, data, aws_account_id, aws_update_tag)
    neo4j_session.execute_write(load_routes_tx, routes, aws_update_tag)
    neo4j_session.execute_write(load_associations_tx, associations, aws_update_tag)


@timeit
def load_route_tables_tx(tx: neo4j.Transaction, data: List[Dict], aws_account_id: str, aws_update_tag: int):
    ingest_route_tables = """
    UNWIND $route_tables as route_table
    MERGE (rtab: EC2RouteTable{id: route_table.RouteTableId})
    ON CREATE SET
        rtab.firstseen = timestamp()
    SET
        rtab.lastupdated = $aws_update_tag,
        rtab.consolelink = route_table.consolelink,
        rtab.arn = route_table.arn,
        rtab.owner_id = route_table.OwnerId,
        rtab.is_default = route_table.isDefault

    WITH route_table, rtab
    MATCH (vpc:AWSVpc{id: route_table.VpcId})
    MERGE (rtab)-[r:MEMBER_OF_AWS_VPC]->(vpc)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $aws_update_tag

    WITH rtab
    MATCH (aws:AWSAccount{id: $aws_account_id})
    MERGE (aws)-[rel:RESOURCE]->(rtab)
    ON CREATE SET rel.firstseen = timestamp()
    SET rel.lastupdated = $aws_update_tag
    """
    tx.run(
        ingest_route_tables,
        route_tables=data,
        aws_account_id=aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def load_routes_tx(tx: neo4j.Transaction, data: List[Dict], aws_update_tag: int):
    ingest_routes = """
    UNWIND $routes as route
    MERGE (rt: EC2Route{id: route.id})
    ON CREATE SET
        rt.firstseen = timestamp()
    SET
        rt.lastupdated = $aws_update_tag,
        rt.destination_cidr_block = route.DestinationCidrBlock,
        rt.destination_ipv6_cidr_block = route.DestinationIpv6CidrBlock,
        rt.gateway_id = route.GatewayId,
        rt.state = route.State,
        rt.nat_gateway_id = route.NatGatewayId
    WITH route, rt
    MATCH (rtab:EC2RouteTable{id: route.RouteTableId})
    MERGE (rtab)-[r:MEMBER_OF_ROUTE_TABLE]->(rt)
    ON CREATE SET
        r.firstseen = timestamp()
    SET
        r.lastupdated = $aws_update_tag
    """
    tx.run(
        ingest_routes,
        routes=data,
        aws_update_tag=aws_update_tag,
    )


@timeit
def load_associations_tx(tx: neo4j.Transaction, data: List[Dict], aws_update_tag: int):
    ingest_associations = """
    UNWIND $associations as assoc
    MERGE (asc:EC2RouteTableAssociation{id: assoc.RouteTableAssociationId})
    ON CREATE SET
        asc.firstseen = timestamp()
    SET
        asc.lastupdated = $aws_update_tag,
        asc.main = assoc.Main,
        asc.Gateway_id = assoc.GatewayId
    WITH assoc, asc
    MATCH (rtab:EC2RouteTable{id: assoc.RouteTableId})
    MERGE (rtab)-[rel:HAS_ASSOCIATION]->(asc)
    ON CREATE SET
        rel.firstseen = timestamp()
    SET
        rel.lastupdated = $aws_update_tag
    WITH asc, assoc
    WHERE assoc.SubnetId IS NOT NULL
    MERGE (subnet:EC2Subnet{subnetid: assoc.SubnetId})
    ON CREATE SET
        subnet.firstseen = timestamp()
    SET
        subnet.lastupdated = $aws_update_tag
    WITH subnet, asc
    MERGE (subnet)-[r:HAS_EXPLICIT_ASSOCIATION]->(asc)
    ON CREATE SET
        r.firstseen = timestamp()
    SET
        r.lastupdated = $aws_update_tag
    """
    tx.run(
        ingest_associations,
        associations=data,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_route_tables(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job('aws_import_ec2_route_table_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync_route_tables(
    neo4j_session: neo4j.Session, boto3_session: boto3.session.Session, regions: List[str],
    current_aws_account_id: str, update_tag: int, common_job_parameters: Dict,
) -> None:
    tic = time.perf_counter()

    logger.info("Syncing EC2 route tables for account '%s', at %s.", current_aws_account_id, tic)

    data = []
    for region in regions:
        logger.info("Syncing EC2 route tables for region '%s' in account '%s'.", region, current_aws_account_id)
        data.extend(get_route_tables_data(boto3_session, region))

    logger.info(f"Total route tables: {len(data)}")

    load_route_tables(neo4j_session, data, current_aws_account_id, update_tag)
    cleanup_route_tables(neo4j_session, common_job_parameters)

    toc = time.perf_counter()
    logger.info(f"Time to process EC2 route tables: {toc - tic:0.4f} seconds")
