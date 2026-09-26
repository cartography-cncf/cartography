import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.intel.aws.util.botocore_config import get_botocore_config
from cartography.models.aws.directconnect.connection import (
    DirectConnectConnectionSchema,
)
from cartography.models.aws.directconnect.gateway import (
    DirectConnectGatewayAssociationSchema,
)
from cartography.models.aws.directconnect.gateway import DirectConnectGatewaySchema
from cartography.models.aws.directconnect.virtual_interface import (
    DirectConnectVirtualInterfaceSchema,
)
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_dx_connections(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = create_boto3_client(
        boto3_session, "directconnect", region_name=region, config=get_botocore_config()
    )
    return client.describe_connections().get("connections", [])


@timeit
@aws_handle_regions
def get_dx_virtual_interfaces(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = create_boto3_client(
        boto3_session, "directconnect", region_name=region, config=get_botocore_config()
    )
    return client.describe_virtual_interfaces().get("virtualInterfaces", [])


@timeit
@aws_handle_regions
def get_dx_gateways(boto3_session: boto3.Session, region: str) -> List[Dict[str, Any]]:
    client = create_boto3_client(
        boto3_session, "directconnect", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("describe_direct_connect_gateways")
    gateways: List[Dict[str, Any]] = []
    for page in paginator.paginate():
        gateways.extend(page.get("directConnectGateways", []))
    return gateways


@timeit
@aws_handle_regions
def get_dx_gateway_associations(
    boto3_session: boto3.Session, region: str, gateways: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Associations are listed per Direct Connect gateway, so this issues one paginated call for
    each gateway found in the region.
    """
    client = create_boto3_client(
        boto3_session, "directconnect", region_name=region, config=get_botocore_config()
    )
    associations: List[Dict[str, Any]] = []
    for gateway in gateways:
        paginator = client.get_paginator("describe_direct_connect_gateway_associations")
        for page in paginator.paginate(
            directConnectGatewayId=gateway["directConnectGatewayId"]
        ):
            associations.extend(page.get("directConnectGatewayAssociations", []))
    return associations


def transform_dx_virtual_interfaces(
    virtual_interfaces: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Flatten the advertised prefixes and the BGP peer states, which the API returns as lists of
    objects, into lists of scalars that Neo4j can store and filter on directly.
    """
    transformed: List[Dict[str, Any]] = []
    for virtual_interface in virtual_interfaces:
        item = dict(virtual_interface)
        item["RouteFilterPrefixes"] = [
            prefix["cidr"]
            for prefix in virtual_interface.get("routeFilterPrefixes") or []
            if prefix.get("cidr")
        ]
        item["BgpPeerStates"] = [
            f"{peer.get('bgpPeerId')}:{peer.get('bgpStatus')}"
            for peer in virtual_interface.get("bgpPeers") or []
        ]
        transformed.append(item)
    return transformed


def transform_dx_gateway_associations(
    associations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Lift the associated gateway out of its nested object and flatten the advertised prefixes.
    `allowedPrefixesToDirectConnectGateway` is what the on-premises network can reach through
    this association, so it is the field that makes the association useful for reachability.
    """
    transformed: List[Dict[str, Any]] = []
    for association in associations:
        item = dict(association)
        associated_gateway = association.get("associatedGateway") or {}
        item["AssociatedGatewayId"] = associated_gateway.get("id") or association.get(
            "virtualGatewayId"
        )
        item["AssociatedGatewayType"] = associated_gateway.get("type")
        item["AssociatedGatewayOwner"] = associated_gateway.get(
            "ownerAccount"
        ) or association.get("virtualGatewayOwnerAccount")
        item["AssociatedGatewayRegion"] = associated_gateway.get(
            "region"
        ) or association.get("virtualGatewayRegion")
        item["AllowedPrefixes"] = [
            prefix["cidr"]
            for prefix in association.get("allowedPrefixesToDirectConnectGateway") or []
            if prefix.get("cidr")
        ]
        transformed.append(item)
    return transformed


@timeit
def load_dx_connections(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.debug(
        "Loading %d Direct Connect connections for region '%s' into graph.",
        len(data),
        region,
    )
    load(
        neo4j_session,
        DirectConnectConnectionSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_dx_gateways(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.debug(
        "Loading %d Direct Connect gateways for region '%s' into graph.",
        len(data),
        region,
    )
    load(
        neo4j_session,
        DirectConnectGatewaySchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_dx_virtual_interfaces(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.debug(
        "Loading %d Direct Connect virtual interfaces for region '%s' into graph.",
        len(data),
        region,
    )
    load(
        neo4j_session,
        DirectConnectVirtualInterfaceSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_dx_gateway_associations(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.debug(
        "Loading %d Direct Connect gateway associations for region '%s' into graph.",
        len(data),
        region,
    )
    load(
        neo4j_session,
        DirectConnectGatewayAssociationSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Running Direct Connect cleanup job.")
    GraphJob.from_node_schema(
        DirectConnectVirtualInterfaceSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        DirectConnectGatewayAssociationSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        DirectConnectConnectionSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(DirectConnectGatewaySchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            "Syncing Direct Connect for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )

        connections = get_dx_connections(boto3_session, region)
        load_dx_connections(
            neo4j_session, connections, region, current_aws_account_id, update_tag
        )

        # Gateways are global, but the API is reached per region and returns the same set
        # each time. Loading is idempotent, so the repetition costs nothing in the graph.
        gateways = get_dx_gateways(boto3_session, region)
        load_dx_gateways(
            neo4j_session, gateways, region, current_aws_account_id, update_tag
        )

        virtual_interfaces = get_dx_virtual_interfaces(boto3_session, region)
        load_dx_virtual_interfaces(
            neo4j_session,
            transform_dx_virtual_interfaces(virtual_interfaces),
            region,
            current_aws_account_id,
            update_tag,
        )

        associations = get_dx_gateway_associations(boto3_session, region, gateways)
        load_dx_gateway_associations(
            neo4j_session,
            transform_dx_gateway_associations(associations),
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
