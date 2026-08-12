import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_paginated
from cartography.intel.render.util import require_non_empty
from cartography.models.render.dedicatedip import RenderDedicatedIPSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, owner_id: str) -> list[dict[str, Any]]:
    return list_paginated(
        session,
        f"{BASE_URL}/dedicated-ips",
        "dedicatedIP",
        params={"ownerId": owner_id},
    )


def transform(dedicated_ips: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Emit one row per (dedicated IP set, associated environment) pair, mirroring
    RenderEnvGroupToServiceRel's pattern - see RenderDedicatedIPToEnvironmentRel's
    docstring. A set with no environmentIds (applies to every service in the
    workspace/region) still emits one row, with `environment_id` unset.
    """
    rows = []
    for dedicated_ip in dedicated_ips:
        dedicated_ip_id = require_non_empty(dedicated_ip.get("id"), "dedicated IP set id")
        base = {
            "id": dedicated_ip_id,
            "name": dedicated_ip.get("name"),
            "description": dedicated_ip.get("description"),
            "ownerId": dedicated_ip.get("ownerId"),
            "region": dedicated_ip.get("region"),
            "ips": dedicated_ip.get("ips"),
            "status": dedicated_ip.get("status"),
            "createdAt": dedicated_ip.get("createdAt"),
            "updatedAt": dedicated_ip.get("updatedAt"),
        }
        environment_ids = dedicated_ip.get("environmentIds") or []
        if not environment_ids:
            rows.append({**base, "environment_id": None})
            continue
        for environment_id in environment_ids:
            rows.append(
                {
                    **base,
                    "environment_id": require_non_empty(
                        environment_id, "dedicated IP set environmentIds entry"
                    ),
                }
            )
    return rows


@timeit
def load_dedicated_ips(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderDedicatedIPSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderDedicatedIPSchema(), common_job_parameters).run(
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
    dedicated_ips = get(session, owner_id)
    transformed = transform(dedicated_ips)
    load_dedicated_ips(neo4j_session, transformed, owner_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
