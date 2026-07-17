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
    AWSTransitGatewayRouteTableAssociationSchema,
    AWSTransitGatewayRouteTablePropagationSchema,
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
        # Skip route tables without an id
        if not rtb_id:
            logger.debug("Skipping TransitGatewayRouteTable without id: %s", rtb)
            continue
        rt_entry: dict[str, Any] = {
            "id": rtb_id,
            "TransitGatewayRouteTableId": rtb_id,
            "TransitGatewayId": rtb.get("TransitGatewayId"),
            # Lowercase key consumed by the TGW->route-table CONTAINS relationship
            # matcher (PropertyRef("transit_gateway_id")). Without this the edge
            # from the AWSTransitGateway node cannot match.
            "transit_gateway_id": rtb.get("TransitGatewayId"),
            "State": rtb.get("State"),
        }
        # Only include Region if present (otherwise use Region passed to load)
        if rtb.get("Region") is not None:
            rt_entry["Region"] = rtb.get("Region")
        route_tables.append(rt_entry)
        # Routes may be under 'Routes' key
        for route in rtb.get("Routes", []) if rtb.get("Routes") else []:
            dest = route.get("DestinationCidrBlock") or route.get("DestinationIpv6CidrBlock") or str(route)
            route_id = f"{rtb_id}|{dest}"
            # The attachment a route points to is nested under
            # TransitGatewayAttachments[]; the search/describe route APIs do not
            # return a top-level TransitGatewayAttachmentId. Use the first
            # attachment's id as the route target for the
            # ROUTES_TO_TGW_ATTACHMENT relationship matcher.
            attachments = route.get("TransitGatewayAttachments") or []
            target = None
            if attachments:
                target = attachments[0].get("TransitGatewayAttachmentId")
            if not target:
                target = route.get("TransitGatewayAttachmentId") or None
            route_entry: dict[str, Any] = {
                "id": route_id,
                "transit_gateway_route_table_id": rtb_id,
                "transit_gateway_id": rtb.get("TransitGatewayId"),
                "destination_cidr_block": route.get("DestinationCidrBlock"),
                "destination_ipv6_cidr_block": route.get("DestinationIpv6CidrBlock"),
                "state": route.get("State"),
                "origin": route.get("Origin"),
                "target": target,
            }
            if rtb.get("Region") is not None:
                route_entry["Region"] = rtb.get("Region")
            routes.append(route_entry)
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
    # Cleanup for associations and propagations
    GraphJob.from_node_schema(AWSTransitGatewayRouteTableAssociationSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(AWSTransitGatewayRouteTablePropagationSchema(), common_job_parameters).run(
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

        # Associations and propagations are fetched per route table (scoped to
        # this region's tables only) to avoid the cartesian duplication that
        # occurred when the fetch re-enumerated route tables on every region
        # iteration. The get_/describe association/propagation APIs do not
        # return the parent route table id, so the fetch helpers inject it and
        # synthesize a stable id (route_table_id|attachment_id) for dedup and
        # relationship matching.
        assoc_list = get_transit_gateway_route_table_associations(
            boto3_session, region, rts
        )
        transformed_assoc = transform_tgw_route_table_associations(assoc_list)
        load_transit_gateway_route_table_associations(
            neo4j_session, transformed_assoc, region, current_aws_account_id, update_tag
        )

        prop_list = get_transit_gateway_route_table_propagations(
            boto3_session, region, rts
        )
        transformed_propagations = transform_tgw_route_table_propagations(prop_list)
        load_transit_gateway_route_table_propagations(
            neo4j_session, transformed_propagations, region, current_aws_account_id, update_tag
        )

    cleanup_transit_gateway_route_tables(neo4j_session, common_job_parameters)


# Association/Propagation helpers

def get_transit_gateway_route_table_associations(
    boto3_session: boto3.session.Session,
    region: str,
    route_tables: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Fetch associations for the given route tables in this region.

    Iterates only the route tables passed in (already fetched for this region)
    rather than re-enumerating, which previously caused per-region cartesian
    duplication. The get_/describe association API does not return the parent
    route table id, so it is injected here and a stable id is synthesized from
    route_table_id|attachment_id for dedup and relationship matching.
    """
    client = create_boto3_client(boto3_session, "ec2", region_name=region, config=get_botocore_config())
    associations: list[dict[str, Any]] = []
    try:
        # Prefer get_ API names if available (newer service models use get_* instead of describe_*)
        api_name = None
        if hasattr(client, "get_transit_gateway_route_table_associations"):
            api_name = "get_transit_gateway_route_table_associations"
        elif hasattr(client, "describe_transit_gateway_route_table_associations"):
            api_name = "describe_transit_gateway_route_table_associations"
        else:
            logger.debug(
                "EC2 client does not support transit gateway route table associations API; skipping associations fallback for region %s",
                region,
            )
            return associations
        for rtb in route_tables:
            rtb_id = rtb.get("TransitGatewayRouteTableId")
            if not rtb_id:
                continue
            next_token = None
            while True:
                params: dict[str, Any] = {"TransitGatewayRouteTableId": rtb_id}
                if next_token:
                    params["NextToken"] = next_token
                resp = getattr(client, api_name)(**params)
                # get_ returns 'Associations'; describe_ returns
                # 'TransitGatewayRouteTableAssociations'. Support both.
                items = resp.get("Associations")
                if items is None:
                    items = resp.get("TransitGatewayRouteTableAssociations", [])
                for item in items:
                    # The API does not echo the parent route table id; inject it
                    # and synthesize a stable id for dedup + matching.
                    item.setdefault("TransitGatewayRouteTableId", rtb_id)
                    attachment = item.get("TransitGatewayAttachmentId") or item.get("ResourceId")
                    if not item.get("TransitGatewayRouteTableAssociationId"):
                        item["TransitGatewayRouteTableAssociationId"] = (
                            f"{rtb_id}|{attachment}" if attachment else None
                        )
                    associations.append(item)
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



def get_transit_gateway_route_table_propagations(
    boto3_session: boto3.session.Session,
    region: str,
    route_tables: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Fetch propagations for the given route tables in this region.

    Iterates only the route tables passed in (already fetched for this region)
    rather than re-enumerating, avoiding per-region cartesian duplication.
    """
    client = create_boto3_client(boto3_session, "ec2", region_name=region, config=get_botocore_config())
    props: list[dict[str, Any]] = []
    try:
        # Prefer get_ API names if available (newer service models use get_* instead of describe_*)
        api_name = None
        if hasattr(client, "get_transit_gateway_route_table_propagations"):
            api_name = "get_transit_gateway_route_table_propagations"
        elif hasattr(client, "describe_transit_gateway_route_table_propagations"):
            api_name = "describe_transit_gateway_route_table_propagations"
        else:
            logger.debug(
                "EC2 client does not support transit gateway route table propagations API; skipping propagations fallback for region %s",
                region,
            )
            return props
        for rtb in route_tables:
            rtb_id = rtb.get("TransitGatewayRouteTableId")
            if not rtb_id:
                continue
            next_token = None
            while True:
                params: dict[str, Any] = {"TransitGatewayRouteTableId": rtb_id}
                if next_token:
                    params["NextToken"] = next_token
                resp = getattr(client, api_name)(**params)
                # The API returns propagation items that may not include a propagation id or the route table id.
                # Attach the TransitGatewayRouteTableId context and generate a stable id if missing.
                items = resp.get("TransitGatewayRouteTablePropagations", [])
                for item in items:
                    # attach route table id context
                    item.setdefault("TransitGatewayRouteTableId", rtb_id)
                    # prefer existing propagation id, otherwise synthesize one from route-table + attachment
                    if not item.get("TransitGatewayRouteTablePropagationId"):
                        attachment = item.get("TransitGatewayAttachmentId") or item.get("ResourceId")
                        item["TransitGatewayRouteTablePropagationId"] = f"{rtb_id}|{attachment}" if attachment else None
                props.extend(items)
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



def transform_tgw_route_table_associations(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    seen: set[str] = set()
    for assoc in data:
        assoc_id = assoc.get("TransitGatewayRouteTableAssociationId")
        # Dedup on the synthesized/real id so the same association fetched more
        # than once does not create duplicate nodes/edges.
        if assoc_id in seen:
            continue
        seen.add(assoc_id)
        # State is flat on the get_ API and nested (AssociationState.State) on
        # some describe_ responses; support both.
        state = assoc.get("State")
        if state is None and isinstance(assoc.get("AssociationState"), dict):
            state = assoc["AssociationState"].get("State")
        transformed.append(
            {
                "id": assoc_id,
                "route_table_id": assoc.get("TransitGatewayRouteTableId"),
                "attachment_id": assoc.get("TransitGatewayAttachmentId"),
                "resource_id": assoc.get("ResourceId"),
                "resource_type": assoc.get("ResourceType"),
                "state": state,
            }
        )
    return transformed


def load_transit_gateway_route_table_associations(neo4j_session: neo4j.Session, data: list[dict[str, Any]], region: str, current_aws_account_id: str, update_tag: int) -> None:
    # Use model-driven load for associations
    # Filter out items missing id first
    filtered = [item for item in data if item.get("id")]
    if not filtered:
        return
    load(
        neo4j_session,
        AWSTransitGatewayRouteTableAssociationSchema(),
        filtered,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


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
    # Use model-driven load for propagations
    filtered = [item for item in data if item.get("id")]
    if not filtered:
        return
    load(
        neo4j_session,
        AWSTransitGatewayRouteTablePropagationSchema(),
        filtered,
        lastupdated=update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )
