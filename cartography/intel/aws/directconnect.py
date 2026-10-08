import logging
from functools import wraps
from typing import Any
from typing import cast
from typing import Dict
from typing import List

import backoff
import boto3
import botocore.exceptions
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
from cartography.util import AWSGetFunc
from cartography.util import is_aws_region_skippable_client_error
from cartography.util import timeit

logger = logging.getLogger(__name__)


class DirectConnectRegionUnreadable(Exception):
    """Raised when a region's Direct Connect data could not be read at all."""


def dx_handle_regions(func: AWSGetFunc) -> AWSGetFunc:
    """
    Like `aws_handle_regions`, but signals an unreadable region with an exception instead of
    an empty list, so `sync` can tell "no Direct Connect here" from "could not look" and skip
    its destructive cleanup in the second case.

    Classification is delegated to `is_aws_region_skippable_client_error` so this stays in
    step with the rest of the AWS intel modules. Anything else, including credential
    failures, propagates.
    """

    @wraps(func)
    @backoff.on_exception(
        backoff.expo,
        botocore.exceptions.ClientError,
        max_time=600,
    )
    def inner_function(*args, **kwargs):  # type: ignore
        try:
            return func(*args, **kwargs)
        except botocore.exceptions.ClientError as error:
            error_code = error.response.get("Error", {}).get("Code")
            if error_code == "InvalidToken":
                raise RuntimeError(
                    "AWS returned an InvalidToken error. Configure regional STS endpoints by "
                    "setting environment variable AWS_STS_REGIONAL_ENDPOINTS=regional or adding "
                    "'sts_regional_endpoints = regional' to your AWS config file."
                ) from error
            if is_aws_region_skippable_client_error(error):
                raise DirectConnectRegionUnreadable(
                    f"Could not read Direct Connect data: {error_code}"
                ) from error
            raise

    return cast(AWSGetFunc, inner_function)


def _paginate_by_token(
    api_call: Any, result_key: str, **kwargs: Any
) -> List[Dict[str, Any]]:
    """
    DescribeConnections and DescribeVirtualInterfaces accept and return `nextToken`, but
    botocore registers no paginator for them, so they are paged by hand here. Without this,
    accounts past the first page silently lose connections or virtual interfaces.
    """
    items: List[Dict[str, Any]] = []
    next_token = None
    while True:
        params = dict(kwargs)
        if next_token:
            params["nextToken"] = next_token
        response = api_call(**params)
        items.extend(response.get(result_key, []))
        next_token = response.get("nextToken")
        if not next_token:
            return items


@timeit
@dx_handle_regions
def get_dx_connections(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = create_boto3_client(
        boto3_session, "directconnect", region_name=region, config=get_botocore_config()
    )
    return _paginate_by_token(client.describe_connections, "connections")


@timeit
@dx_handle_regions
def get_dx_virtual_interfaces(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = create_boto3_client(
        boto3_session, "directconnect", region_name=region, config=get_botocore_config()
    )
    return _paginate_by_token(client.describe_virtual_interfaces, "virtualInterfaces")


@timeit
@dx_handle_regions
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
@dx_handle_regions
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
    cleanup_safe = True
    unreadable_regions: List[str] = []

    # Direct Connect gateways and their associations are global. Fetch them once, from the
    # first region that answers, rather than once per region: the result is identical and
    # repeating it only costs API calls and write traffic.
    gateways: List[Dict[str, Any]] = []
    associations: List[Dict[str, Any]] = []
    gateways_region: str | None = None
    for region in regions:
        try:
            gateways = get_dx_gateways(boto3_session, region)
            associations = get_dx_gateway_associations(boto3_session, region, gateways)
            gateways_region = region
            break
        except DirectConnectRegionUnreadable as error:
            logger.warning(
                "Could not read Direct Connect gateways from region '%s' for account '%s': %s",
                region,
                current_aws_account_id,
                error,
            )

    if gateways_region is None:
        # No region answered, so the global objects were never read. Skip cleanup rather
        # than delete what a previous run found.
        cleanup_safe = False
        logger.error(
            "Could not read Direct Connect gateways in any of the %d requested regions for "
            "account '%s'. Direct Connect is likely denied account-wide, or the role lacks "
            "Direct Connect permissions.",
            len(regions),
            current_aws_account_id,
        )
    else:
        load_dx_gateways(
            neo4j_session, gateways, gateways_region, current_aws_account_id, update_tag
        )
        load_dx_gateway_associations(
            neo4j_session,
            transform_dx_gateway_associations(associations),
            gateways_region,
            current_aws_account_id,
            update_tag,
        )

    # Connections and virtual interfaces are regional.
    for region in regions:
        logger.info(
            "Syncing Direct Connect for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        try:
            connections = get_dx_connections(boto3_session, region)
            virtual_interfaces = get_dx_virtual_interfaces(boto3_session, region)
        except DirectConnectRegionUnreadable as error:
            cleanup_safe = False
            unreadable_regions.append(region)
            logger.warning(
                "Skipping Direct Connect region '%s' for account '%s': %s",
                region,
                current_aws_account_id,
                error,
            )
            continue

        load_dx_connections(
            neo4j_session, connections, region, current_aws_account_id, update_tag
        )
        load_dx_virtual_interfaces(
            neo4j_session,
            transform_dx_virtual_interfaces(virtual_interfaces),
            region,
            current_aws_account_id,
            update_tag,
        )

    if cleanup_safe:
        cleanup(neo4j_session, common_job_parameters)
    else:
        logger.warning(
            "Skipping Direct Connect cleanup for account '%s' because %s could not be read. "
            "Preserving last-known-good data.",
            current_aws_account_id,
            (
                ", ".join(unreadable_regions)
                if unreadable_regions
                else "the global gateways"
            ),
        )
