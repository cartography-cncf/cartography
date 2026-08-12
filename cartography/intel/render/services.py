import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_paginated
from cartography.intel.render.util import require_non_empty
from cartography.models.render.service import RenderServiceSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, owner_id: str) -> list[dict[str, Any]]:
    return list_paginated(
        session,
        f"{BASE_URL}/services",
        "service",
        params={"ownerId": [owner_id]},
    )


def transform(services: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transformed = []
    for service in services:
        details = service.get("serviceDetails") or {}
        transformed.append(
            {
                "id": require_non_empty(service.get("id"), "service id"),
                "name": service.get("name"),
                "ownerId": service.get("ownerId"),
                "environmentId": service.get("environmentId"),
                "type": service.get("type"),
                "slug": service.get("slug"),
                "repo": service.get("repo"),
                "branch": service.get("branch"),
                "rootDir": service.get("rootDir"),
                "dashboardUrl": service.get("dashboardUrl"),
                "suspended": service.get("suspended"),
                "autoDeploy": service.get("autoDeploy"),
                "runtime": details.get("runtime"),
                "plan": details.get("plan"),
                "region": details.get("region"),
                "url": details.get("url"),
                "numInstances": details.get("numInstances"),
                "createdAt": service.get("createdAt"),
                "updatedAt": service.get("updatedAt"),
            }
        )
    return transformed


@timeit
def load_services(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderServiceSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderServiceSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    owner_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> tuple[list[str], list[dict[str, Any]]]:
    """
    Sync the services belonging to a single Render workspace.

    :return: A tuple of (service ids, raw un-transformed service objects). The ids let
        the caller fetch custom domains and secret files; the raw objects let the caller
        read each service's embedded `ipAllowList` without a second network call.
    """
    services = get(session, owner_id)
    transformed = transform(services)
    load_services(neo4j_session, transformed, owner_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return [service["id"] for service in transformed], services
