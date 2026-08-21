import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_paginated
from cartography.intel.render.util import require_non_empty
from cartography.models.render.blueprint import RenderBlueprintSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Maps a blueprint resources[] entry's `type` to the row key that carries its id, so
# RenderBlueprintSchema's four conditional relationships (see
# cartography/models/render/blueprint.py) each resolve against the right node label.
# Resource types with no entry here (e.g. `artifact_source`) are not modeled by this
# module, so a row for one of those carries no linked id and produces no edge.
_RESOURCE_TYPE_TO_ROW_KEY = {
    "static_site": "service_id",
    "web_service": "service_id",
    "private_service": "service_id",
    "background_worker": "service_id",
    "cron_job": "service_id",
    "redis": "key_value_id",
    "key_value": "key_value_id",
    "postgres": "postgres_id",
    "environment_group": "env_group_id",
}


@timeit
def get(session: requests.Session, owner_id: str) -> list[dict[str, Any]]:
    return list_paginated(
        session,
        f"{BASE_URL}/blueprints",
        "blueprint",
        params={"ownerId": [owner_id]},
    )


def transform(blueprints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Emit one row per (blueprint, resource) pair, mirroring RenderIPAllowRule's
    conditional-match pattern: each row has at most one of service_id / postgres_id /
    key_value_id / env_group_id populated, and the corresponding relationship in
    RenderBlueprintSchema resolves only that one edge. A blueprint with no resources -
    or whose resources are all of an unmodeled type - still emits one row with no
    linked ids, so the blueprint node itself is not lost.
    """
    rows = []
    for blueprint in blueprints:
        blueprint_id = require_non_empty(blueprint.get("id"), "blueprint id")
        base = {
            "id": blueprint_id,
            "name": blueprint.get("name"),
            "ownerId": blueprint.get("ownerId"),
            "status": blueprint.get("status"),
            "autoSync": blueprint.get("autoSync"),
            "repo": blueprint.get("repo"),
            "branch": blueprint.get("branch"),
            "path": blueprint.get("path"),
            "lastSync": blueprint.get("lastSync"),
        }
        empty_links = {
            "service_id": None,
            "postgres_id": None,
            "key_value_id": None,
            "env_group_id": None,
        }
        resources = blueprint.get("resources") or []
        if not resources:
            rows.append({**base, **empty_links})
            continue
        for resource in resources:
            resource_id = require_non_empty(
                resource.get("id"), "blueprint resources entry id"
            )
            resource_type = require_non_empty(
                resource.get("type"), "blueprint resources entry type"
            )
            # A recognized-but-unmodeled type (e.g. artifact_source) is legitimate and
            # intentionally produces no linked id - see _RESOURCE_TYPE_TO_ROW_KEY's
            # comment. Only a missing type is malformed data, checked above.
            row_key = _RESOURCE_TYPE_TO_ROW_KEY.get(resource_type)
            row = {**base, **empty_links}
            if row_key:
                row[row_key] = resource_id
            rows.append(row)
    return rows


@timeit
def load_blueprints(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderBlueprintSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderBlueprintSchema(), common_job_parameters).run(
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
    blueprints = get(session, owner_id)
    transformed = transform(blueprints)
    load_blueprints(neo4j_session, transformed, owner_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
