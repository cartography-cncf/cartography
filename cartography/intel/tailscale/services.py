import json
import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.tailscale.service import TailscaleServiceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

_TIMEOUT = 30


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: Dict[str, Any],
    org: str,
) -> List[Dict[str, Any]]:
    """
    Sync Tailscale Services.

    Fetches services from the Tailscale API, transforms them, and loads
    them into the graph as TailscaleService nodes connected to their
    TailscaleTailnet and any associated TailscaleTag nodes.

    Returns the raw service data for use by other modules (e.g., grants).
    """
    logger.info("Starting Tailscale Services sync")
    raw_services = get(api_session, common_job_parameters["BASE_URL"], org)
    transformed = transform(raw_services)
    load_services(neo4j_session, transformed, org, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
    logger.info("Completed Tailscale Services sync: %d services", len(transformed))
    return raw_services


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org: str,
) -> List[Dict[str, Any]]:
    """Fetch services from the Tailscale API.

    GET /api/v2/tailnet/{tailnet}/services
    """
    req = api_session.get(
        f"{base_url}/tailnet/{org}/services",
        timeout=_TIMEOUT,
    )
    req.raise_for_status()
    return req.json().get("vipServices", [])


def transform(
    raw_services: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Transform raw API data into the format expected by the data model.

    - Extracts IPv4/IPv6 from the addrs list
    - Serializes ports list to JSON string for storage
    - Normalizes tags to match TailscaleTag IDs (tag:xxx)
    - Builds the id as svc:<name> to match the grant selector format
    """
    transformed: List[Dict[str, Any]] = []
    for service in raw_services:
        name = service.get("name", "")
        addrs = service.get("addrs", [])
        tags = service.get("tags", [])

        transformed.append(
            {
                "id": f"svc:{name}",
                "name": name,
                "comment": service.get("comment"),
                "ipv4_address": addrs[0] if len(addrs) > 0 else None,
                "ipv6_address": addrs[1] if len(addrs) > 1 else None,
                "ports": json.dumps(service.get("ports", []), sort_keys=True),
                "tags": json.dumps(tags, sort_keys=True) if tags else None,
                "tag_ids": tags,
            },
        )
    return transformed


@timeit
def load_services(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org: str,
    update_tag: int,
) -> None:
    logger.info("Loading %d Tailscale Services to the graph", len(data))
    load(
        neo4j_session,
        TailscaleServiceSchema(),
        data,
        lastupdated=update_tag,
        org=org,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        TailscaleServiceSchema(),
        common_job_parameters,
    ).run(neo4j_session)
