import json
import logging
from typing import Any

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
    common_job_parameters: dict[str, Any],
    org: str,
) -> list[dict[str, Any]]:
    """
    Sync Tailscale Services.

    Fetches services from the Tailscale API, transforms them, and loads
    them into the graph as TailscaleService nodes connected to their
    TailscaleTailnet and any associated TailscaleTag nodes.

    Returns the raw service data for use by other modules (e.g., grants).
    """
    raw_services = get(api_session, common_job_parameters["BASE_URL"], org)
    transformed = transform(raw_services)
    load_services(neo4j_session, transformed, org, common_job_parameters["UPDATE_TAG"])
    cleanup(neo4j_session, common_job_parameters)
    return raw_services


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
    org: str,
) -> list[dict[str, Any]]:
    """Fetch services from the Tailscale API.

    GET /api/v2/tailnet/{tailnet}/services
    """
    req = api_session.get(
        f"{base_url}/tailnet/{org}/services",
        timeout=_TIMEOUT,
    )
    if req.status_code == 404:
        logger.warning(
            "Tailscale Services endpoint returned 404 for tailnet %s; "
            "skipping (Services may not be enabled for this tailnet).",
            org,
        )
        return []
    req.raise_for_status()
    return req.json()["vipServices"]


def transform(
    raw_services: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Transform raw API data into the format expected by the data model.

    - Extracts IPv4/IPv6 from the addrs list
    - Serializes ports list to JSON string for storage
    - Normalizes tags to match TailscaleTag IDs (tag:xxx)
    - Builds the id as svc:<name> to match the grant selector format
    """
    transformed: list[dict[str, Any]] = []
    for service in raw_services:
        name = service["name"]
        service_id = _normalize_service_id(name)
        addrs = service.get("addrs", [])
        tags = service.get("tags", [])

        transformed.append(
            {
                "id": service_id,
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


def _normalize_service_id(name: str) -> str:
    return name if name.startswith("svc:") else f"svc:{name}"


@timeit
def load_services(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    org: str,
    update_tag: int,
) -> None:
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
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(
        TailscaleServiceSchema(),
        common_job_parameters,
    ).run(neo4j_session)
