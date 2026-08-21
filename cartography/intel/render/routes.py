import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_paginated
from cartography.intel.render.util import require_non_empty
from cartography.models.render.route import RenderRouteSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, service_id: str) -> list[dict[str, Any]]:
    return list_paginated(
        session,
        f"{BASE_URL}/services/{service_id}/routes",
        "route",
    )


def transform(
    routes: list[dict[str, Any]], service_id: str, owner_id: str
) -> list[dict[str, Any]]:
    return [
        {
            "id": require_non_empty(route.get("id"), "route id"),
            "ownerId": owner_id,
            "serviceId": service_id,
            "type": route.get("type"),
            "source": route.get("source"),
            "destination": route.get("destination"),
            "priority": route.get("priority"),
        }
        for route in routes
    ]


@timeit
def load_routes(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderRouteSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderRouteSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    owner_id: str,
    services: list[dict[str, Any]],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    all_routes: list[dict[str, Any]] = []
    for service in services:
        # Redirect/rewrite rules are a static-site-only feature
        # (https://render.com/docs/redirects-rewrites), the same as custom response
        # headers - see headerrules.py. Every other service type runs its own server
        # and has no comparable Render-managed feature; calling this endpoint for
        # those types is expected to 404.
        if service.get("type") != "static_site":
            continue
        service_id = service["id"]
        routes = get(session, service_id)
        all_routes.extend(transform(routes, service_id, owner_id))
    load_routes(neo4j_session, all_routes, owner_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
