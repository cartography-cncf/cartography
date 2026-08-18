import ipaddress
import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.flyio.util import get_next_cursor
from cartography.intel.flyio.util import post_graphql
from cartography.models.flyio.ip import FlyIPSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

FLY_INGRESS_IPS_QUERY = """
query ($appName: String!, $limit: Int!, $after: String) {
  app(name: $appName) {
    ipAddresses(first: $limit, after: $after) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        id
        address
        type
        region
        createdAt
        serviceName
        network {
          name
          organization {
            slug
          }
        }
      }
    }
    sharedIpAddress
  }
}
"""

FLY_EGRESS_IPS_QUERY = """
query ($appName: String!, $limit: Int!, $after: String) {
  app(name: $appName) {
    egressIpAddresses(first: $limit, after: $after) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        id
        ip
        version
        region
        updatedAt
      }
    }
  }
}
"""


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    response = get(
        api_session,
        common_job_parameters["GRAPHQL_URL"],
        common_job_parameters["APP_NAME"],
    )
    ips = transform(response, common_job_parameters["APP_ID"])
    load_ips(
        neo4j_session,
        ips,
        common_job_parameters["APP_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)
    return ips


@timeit
def get(
    api_session: requests.Session,
    graphql_url: str,
    app_name: str,
    page_size: int = 100,
) -> dict[str, Any]:
    ingress_response = _get_ip_connection(
        api_session,
        graphql_url,
        FLY_INGRESS_IPS_QUERY,
        app_name,
        "ipAddresses",
        page_size,
    )
    egress_ips = _get_ip_connection(
        api_session,
        graphql_url,
        FLY_EGRESS_IPS_QUERY,
        app_name,
        "egressIpAddresses",
        page_size,
    )["nodes"]
    return {
        "app": {
            "ipAddresses": {"nodes": ingress_response["nodes"]},
            "sharedIpAddress": ingress_response["sharedIpAddress"],
            "egressIpAddresses": {"nodes": egress_ips},
        },
    }


def _get_ip_connection(
    api_session: requests.Session,
    graphql_url: str,
    query: str,
    app_name: str,
    connection_name: str,
    page_size: int,
) -> dict[str, Any]:
    ips: list[dict[str, Any]] = []
    shared_ip_address = None
    after: str | None = None
    while True:
        response = post_graphql(
            api_session,
            graphql_url,
            query,
            {"appName": app_name, "limit": page_size, "after": after},
        )
        app = response.get("app") or {}
        connection = app.get(connection_name) or {}
        ips.extend(connection.get("nodes") or [])
        if "sharedIpAddress" in app:
            shared_ip_address = app.get("sharedIpAddress")
        after = get_next_cursor(
            connection.get("pageInfo") or {},
            after,
            connection_name,
        )
        if not after:
            return {
                "nodes": ips,
                "sharedIpAddress": shared_ip_address,
            }


def transform(response: dict[str, Any], app_id: str) -> list[dict[str, Any]]:
    app = response.get("app") or {}
    ip_addresses = app.get("ipAddresses") or {}
    ips = [
        _transform_ingress_ip(ip_address, app_id)
        for ip_address in ip_addresses.get("nodes") or []
    ]

    shared_ip_address = app.get("sharedIpAddress")
    if shared_ip_address and not any(ip["address"] == shared_ip_address for ip in ips):
        ips.append(
            _build_ip(
                address=shared_ip_address,
                app_id=app_id,
                ip_type="shared_v4",
                direction="ingress",
            ),
        )

    egress_ip_addresses = app.get("egressIpAddresses") or {}
    for ip_address in egress_ip_addresses.get("nodes") or []:
        ips.append(_transform_egress_ip(ip_address, app_id))

    return ips


def _transform_ingress_ip(
    ip_address: dict[str, Any],
    app_id: str,
) -> dict[str, Any]:
    network = ip_address.get("network") or {}
    organization = network.get("organization") or {}
    return _build_ip(
        address=ip_address["address"],
        app_id=app_id,
        ip_id=ip_address.get("id"),
        ip_type=ip_address.get("type"),
        region=ip_address.get("region"),
        created_at=ip_address.get("createdAt"),
        direction="ingress",
        service_name=ip_address.get("serviceName"),
        network_name=network.get("name"),
        network_organization_slug=organization.get("slug"),
    )


def _transform_egress_ip(
    ip_address: dict[str, Any],
    app_id: str,
) -> dict[str, Any]:
    version = ip_address.get("version")
    return _build_ip(
        address=ip_address["ip"],
        app_id=app_id,
        ip_id=ip_address.get("id"),
        ip_type=f"egress_v{version}" if version else "egress",
        region=ip_address.get("region"),
        created_at=ip_address.get("updatedAt"),
        direction="egress",
    )


def _build_ip(
    *,
    address: str,
    app_id: str,
    ip_id: str | None = None,
    ip_type: str | None = None,
    region: str | None = None,
    created_at: str | None = None,
    direction: str,
    service_name: str | None = None,
    network_name: str | None = None,
    network_organization_slug: str | None = None,
) -> dict[str, Any]:
    parsed_ip = ipaddress.ip_address(address)
    return {
        "id": ip_id or f"{app_id}/{address}",
        "address": address,
        "type": ip_type,
        "region": region,
        "created_at": created_at,
        "direction": direction,
        "ip_version": parsed_ip.version,
        "is_public": parsed_ip.is_global,
        "service_name": service_name,
        "network_name": network_name,
        "network_organization_slug": network_organization_slug,
    }


@timeit
def load_ips(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    app_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        FlyIPSchema(),
        data,
        lastupdated=update_tag,
        APP_ID=app_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(FlyIPSchema(), common_job_parameters).run(
        neo4j_session,
    )
