import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_paginated
from cartography.intel.render.util import require_non_empty
from cartography.models.render.envgroup import RenderEnvGroupSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, owner_id: str) -> list[dict[str, Any]]:
    # Env group contents (env var values, secret file contents) are never fetched here -
    # only this metadata endpoint is called.
    return list_paginated(
        session,
        f"{BASE_URL}/env-groups",
        "envGroup",
        params={"ownerId": [owner_id]},
    )


def transform(env_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Emit one row per (env group, linked service) pair, so a group linked to several
    services produces several rows sharing the same group id - see
    RenderEnvGroupToServiceRel's docstring for why that is how the relationship resolves.
    A group with no linked services still emits one row, with `service_id` unset, so the
    group node itself is not lost.
    """
    rows = []
    for group in env_groups:
        group_id = require_non_empty(group.get("id"), "env group id")
        base = {
            "id": group_id,
            "name": group.get("name"),
            "ownerId": group.get("ownerId"),
            "environmentId": group.get("environmentId"),
            "createdAt": group.get("createdAt"),
            "updatedAt": group.get("updatedAt"),
        }
        service_links = group.get("serviceLinks") or []
        if not service_links:
            rows.append({**base, "service_id": None})
            continue
        for link in service_links:
            rows.append(
                {
                    **base,
                    "service_id": require_non_empty(
                        link.get("id"), "env group serviceLinks entry id"
                    ),
                }
            )
    return rows


@timeit
def load_env_groups(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderEnvGroupSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderEnvGroupSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    owner_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    env_groups = get(session, owner_id)
    transformed = transform(env_groups)
    load_env_groups(neo4j_session, transformed, owner_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
