import logging
from typing import Any

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load, run_write_query
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
        # search_transit_gateway_routes may not have a paginator in all botocore versions.
        next_token = None
        state_values = ["active", "blackhole", "pending", "deleting", "deleted"]
        while True:
            params: dict[str, Any] = {
                "TransitGatewayRouteTableId": route_table_id,
                "Filters": [{"Name": "state", "Values": state_values}],
            }
            if next_token:
                params["NextToken"] = next_token
            resp = client.search_transit_gateway_routes(**params)
            routes.extend(resp.get("Routes", []))
            next_token = resp.get("NextToken")
            if not next_token:
                break
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

        # Load associations and propagations — prefer values present on the described RTBs
        assoc_list: list[dict[str, Any]] = []
        for rtb in rts:
            assoc_list.extend(rtb.get("Associations", []))
        if not assoc_list:
            assoc_list = get_transit_gateway_route_table_associations(boto3_session, region)
        transformed_assoc = transform_tgw_route_table_associations(assoc_list)
        load_transit_gateway_route_table_associations(
            neo4j_session, transformed_assoc, region, current_aws_account_id, update_tag
        )

        prop_list: list[dict[str, Any]] = []
        for rtb in rts:
            # Some describe responses include PropagatingVgws; use that if present
            prop_list.extend(rtb.get("PropagatingVgws", []))
        if not prop_list:
            prop_list = get_transit_gateway_route_table_propagations(boto3_session, region)
        transformed_propagations = transform_tgw_route_table_propagations(prop_list)
        load_transit_gateway_route_table_propagations(
            neo4j_session, transformed_propagations, region, current_aws_account_id, update_tag
        )

    cleanup_transit_gateway_route_tables(neo4j_session, common_job_parameters)


# Association/Propagation helpers

def get_transit_gateway_route_table_associations(boto3_session: boto3.session.Session, region: str) -> list[dict[str, Any]]:
    client = create_boto3_client(boto3_session, "ec2", region_name=region, config=get_botocore_config())
    associations: list[dict[str, Any]] = []
    try:
        # describe_transit_gateway_route_table_associations may not be pageable via botocore paginator in all versions.
        next_token = None
        while True:
            params: dict[str, Any] = {}
            if next_token:
                params["NextToken"] = next_token
            resp = client.describe_transit_gateway_route_table_associations(**params)
            associations.extend(resp.get("TransitGatewayRouteTableAssociations", []))
            next_token = resp.get("NextToken")
            if not next_token:
                break
    except botocore.exceptions.ClientError as e:
        logger.warning(
            "Could not retrieve Transit Gateway route table associations due to boto3 error %s: %s. Skipping.",
            e.response.get("Error", {}).get("Code"),
            e.response.get("Error", {}).get("Message"),
        )
    return associations


def transform_tgw_route_table_associations(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for assoc in data:
        transformed.append(
            {
                "id": assoc.get("TransitGatewayRouteTableAssociationId"),
                "route_table_id": assoc.get("TransitGatewayRouteTableId"),
                "attachment_id": assoc.get("TransitGatewayAttachmentId"),
                "resource_id": assoc.get("ResourceId"),
                "resource_type": assoc.get("ResourceType"),
                "state": assoc.get("AssociationState", {}).get("State"),
            }
        )
    return transformed


def load_transit_gateway_route_table_associations(neo4j_session: neo4j.Session, data: list[dict[str, Any]], region: str, current_aws_account_id: str, update_tag: int) -> None:
    # For now load as simple nodes/relationships using a custom query; this can be replaced with model-driven load later
    for item in data:
        run_write_query(
            neo4j_session,
            """
            MERGE (a:AWSTransitGatewayRouteTableAssociation{id: $id})
            SET a.route_table_id = $route_table_id, a.attachment_id = $attachment_id, a.resource_id = $resource_id, a.resource_type = $resource_type, a.state = $state, a.Region = $Region, a.lastupdated = $lastupdated
            WITH a
            MATCH (rt:AWSTransitGatewayRouteTable{TransitGatewayRouteTableId: $route_table_id})
            MERGE (rt)<-[:RESOURCE]-(a)
            """,
            id=item.get("id"),
            route_table_id=item.get("route_table_id"),
            attachment_id=item.get("attachment_id"),
            resource_id=item.get("resource_id"),
            resource_type=item.get("resource_type"),
            state=item.get("state"),
            Region=region,
            lastupdated=update_tag,
        )


def get_transit_gateway_route_table_propagations(boto3_session: boto3.session.Session, region: str) -> list[dict[str, Any]]:
    client = create_boto3_client(boto3_session, "ec2", region_name=region, config=get_botocore_config())
    props: list[dict[str, Any]] = []
    try:
        # describe_transit_gateway_route_table_propagations may not be pageable via botocore paginator in all versions.
        next_token = None
        while True:
            params: dict[str, Any] = {}
            if next_token:
                params["NextToken"] = next_token
            resp = client.describe_transit_gateway_route_table_propagations(**params)
            props.extend(resp.get("TransitGatewayRouteTablePropagations", []))
            next_token = resp.get("NextToken")
            if not next_token:
                break
    except botocore.exceptions.ClientError as e:
        logger.warning(
            "Could not retrieve Transit Gateway route table propagations due to boto3 error %s: %s. Skipping.",
            e.response.get("Error", {}).get("Code"),
            e.response.get("Error", {}).get("Message"),
        )
    return props


def transform_tgw_route_table_propagations(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for p in data:
        transformed.append(
            {
                "id": p.get("TransitGatewayRouteTablePropagationId"),
                "route_table_id": p.get("TransitGatewayRouteTableId"),
                "attachment_id": p.get("TransitGatewayAttachmentId"),
                "state": p.get("State"),
            }
        )
    return transformed


def load_transit_gateway_route_table_propagations(neo4j_session: neo4j.Session, data: list[dict[str, Any]], region: str, current_aws_account_id: str, update_tag: int) -> None:
    for item in data:
        run_write_query(
            neo4j_session,
            """
            MERGE (p:AWSTransitGatewayRouteTablePropagation{id: $id})
            SET p.route_table_id = $route_table_id, p.attachment_id = $attachment_id, p.state = $state, p.Region = $Region, p.lastupdated = $lastupdated
            WITH p
            MATCH (rt:AWSTransitGatewayRouteTable{TransitGatewayRouteTableId: $route_table_id})
            MERGE (rt)<-[:PROPAGATED_BY]-(p)
            """,
            id=item.get("id"),
            route_table_id=item.get("route_table_id"),
            attachment_id=item.get("attachment_id"),
            state=item.get("state"),
            Region=region,
            lastupdated=update_tag,
        )
