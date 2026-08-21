import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_paginated
from cartography.intel.render.util import require_non_empty
from cartography.models.render.keyvalue import RenderKeyValueSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, owner_id: str) -> list[dict[str, Any]]:
    return list_paginated(
        session,
        f"{BASE_URL}/key-value",
        "keyValue",
        params={"ownerId": [owner_id]},
    )


def transform(instances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": require_non_empty(instance.get("id"), "key value id"),
            "name": instance.get("name"),
            "ownerId": (instance.get("owner") or {}).get("id"),
            "environmentId": instance.get("environmentId"),
            "status": instance.get("status"),
            "region": instance.get("region"),
            "plan": instance.get("plan"),
            "version": instance.get("version"),
            "dashboardUrl": instance.get("dashboardUrl"),
            "createdAt": instance.get("createdAt"),
            "updatedAt": instance.get("updatedAt"),
        }
        for instance in instances
    ]


@timeit
def load_key_value_instances(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderKeyValueSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderKeyValueSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    owner_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Sync the Key Value instances belonging to a single Render workspace.

    :return: The raw (un-transformed) instance objects, so the caller can read their
        embedded `ipAllowList` without a second network call.
    """
    instances = get(session, owner_id)
    transformed = transform(instances)
    load_key_value_instances(neo4j_session, transformed, owner_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return instances
