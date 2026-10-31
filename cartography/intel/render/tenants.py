import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_paginated
from cartography.intel.render.util import require_non_empty
from cartography.models.render.tenant import RenderTenantSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session) -> list[dict[str, Any]]:
    return list_paginated(session, f"{BASE_URL}/owners", "owner")


def transform(owners: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": require_non_empty(owner.get("id"), "owner id"),
            "name": owner.get("name"),
            "email": owner.get("email"),
            "type": owner.get("type"),
        }
        for owner in owners
    ]


@timeit
def load_tenants(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderTenantSchema(),
        data,
        lastupdated=update_tag,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderTenantSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Sync every Render workspace (`owner`) reachable by the configured API key.

    :return: The synced tenants, so the caller can fan out per-workspace syncs.
    """
    owners = get(session)
    tenants = transform(owners)
    load_tenants(neo4j_session, tenants, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return tenants
