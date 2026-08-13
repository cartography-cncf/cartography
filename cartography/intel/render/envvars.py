import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_paginated
from cartography.intel.render.util import require_non_empty
from cartography.models.render.envvar import RenderEnvVarSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, service_id: str) -> list[dict[str, Any]]:
    # Render's response includes each env var's full plaintext `value` alongside its
    # `key`. transform() below discards `value` immediately and it is never logged,
    # stored, or passed to load() - only the key is ingested. Mirrors secretfiles.py.
    return list_paginated(
        session,
        f"{BASE_URL}/services/{service_id}/env-vars",
        "envVar",
    )


def transform(
    env_vars: list[dict[str, Any]], service_id: str, owner_id: str
) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{service_id}/{require_non_empty(env_var.get('key'), 'env var key')}",
            "key": env_var.get("key"),
            "ownerId": owner_id,
            "serviceId": service_id,
        }
        for env_var in env_vars
    ]


@timeit
def load_env_vars(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderEnvVarSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderEnvVarSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    owner_id: str,
    service_ids: list[str],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    all_env_vars: list[dict[str, Any]] = []
    for service_id in service_ids:
        env_vars = get(session, service_id)
        all_env_vars.extend(transform(env_vars, service_id, owner_id))
    load_env_vars(neo4j_session, all_env_vars, owner_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
