import logging
from typing import Any

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.models.aws.ec2.tgw_route_tables import (
    AWSTransitGatewayRouteTableSchema,
    AWSTransitGatewayRouteSchema,
)
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_transit_gateway_route_tables(
    boto3_session: boto3.session.Session, region: str
) -> list[dict[str, Any]]:
    client = create_boto3_client(
        boto3_session, "ec2", region_name=region, config=get_botocore_config()
    )
    route_tables: list[dict[str, Any]] = []
    try:
        paginator = client.get_paginator("describe_transit_gateway_route_tables")
        for page in paginator.paginate():
            route_tables.extend(page.get("TransitGatewayRouteTables", []))
    except botocore.exceptions.ClientError as e:
        logger.warning(
            "Could not retrieve Transit Gateway Route Tables due to boto3 error %s: %s. Skipping.",
            e.response["Error"]["Code"],
            e.response["Error"]["Message"],
        )
    return route_tables


def get_transit_gateway_routes_for_table(
    boto3_session: boto3.session.Session, region: str, route_table_id: str
) -> list[dict[str, Any]]:
    """Search Transit Gateway routes for a specific route table as a fallback when
    describe_transit_gateway_route_tables does not include Routes in the response.
    """
    client = create_boto3_client(
        boto3_session, "ec2", region_name=region, config=get_botocore_config()
    )
    routes: list[dict[str, Any]] = []
    try:
        paginator = client.get_paginator("search_transit_gateway_routes")
        for page in paginator.paginate(TransitGatewayRouteTableId=route_table_id):
            routes.extend(page.get("Routes", []))
    except botocore.exceptions.ClientError as e:
        logger.warning(
            "Could not search Transit Gateway routes for %s due to boto3 error %s: %s. Skipping.",
            route_table_id,
            e.response.get("Error", {}).get("Code"),
            e.response.get("Error", {}).get("Message"),
        )
    return routes


def transform_tgw_route_tables(data: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    route_tables: list[dict[str, Any]] = []
    routes: list[dict[str, Any]] = []
    for rtb in data:
        rtb_id = rtb.get("TransitGatewayRouteTableId")
        route_tables.append(
            {
                "id": rtb_id,
                "TransitGatewayRouteTableId": rtb_id,
                "TransitGatewayId": rtb.get("TransitGatewayId"),
                "State": rtb.get("State"),
                "Region": rtb.get("Region"),
            }
        )
        # Routes may be under 'Routes' key
        for route in rtb.get("Routes", []) if rtb.get("Routes") else []:
            # build simple id from rtb + destination
            dest = route.get("DestinationCidrBlock") or route.get("DestinationIpv6CidrBlock") or str(route)
            route_id = f"{rtb_id}|{dest}"
            routes.append(
                {
                    "id": route_id,
                    "transit_gateway_route_table_id": rtb_id,
                    "transit_gateway_id": rtb.get("TransitGatewayId"),
                    "destination_cidr_block": route.get("DestinationCidrBlock"),
                    "destination_ipv6_cidr_block": route.get("DestinationIpv6CidrBlock"),
                    "state": route.get("State"),
                    "origin": route.get("Origin"),
                    "target": route.get("TransitGatewayAttachmentId") or route.get("TransitGatewayRouteTableAnnouncementId") or None,
                    "Region": rtb.get("Region"),
                }
            )
    return route_tables, routes


@timeit
def load_transit_gateway_route_tables(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSTransitGatewayRouteTableSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_transit_gateway_routes(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSTransitGatewayRouteSchema(),
        data,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup_transit_gateway_route_tables(
    neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]
) -> None:
    logger.debug("Running TGW route tables cleanup")
    GraphJob.from_node_schema(AWSTransitGatewayRouteTableSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(AWSTransitGatewayRouteSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync_transit_gateway_route_tables(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing AWS Transit Gateway Route Tables for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        rts = get_transit_gateway_route_tables(boto3_session, region)
        # Fallback: if describe response lacks 'Routes', call the search API per table
        for rtb in rts:
            if not rtb.get("Routes"):
                rtb_id = rtb.get("TransitGatewayRouteTableId")
                if rtb_id:
                    rtb["Routes"] = get_transit_gateway_routes_for_table(
                        boto3_session, region, rtb_id
                    )
        rtb_data, route_data = transform_tgw_route_tables(rts)
        load_transit_gateway_routes(neo4j_session, route_data, region, current_aws_account_id, update_tag)
        load_transit_gateway_route_tables(neo4j_session, rtb_data, region, current_aws_account_id, update_tag)
    cleanup_transit_gateway_route_tables(neo4j_session, common_job_parameters)
