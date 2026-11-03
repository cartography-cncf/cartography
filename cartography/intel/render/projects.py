import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_paginated
from cartography.intel.render.util import require_non_empty
from cartography.models.render.project import RenderProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, owner_id: str) -> list[dict[str, Any]]:
    return list_paginated(
        session,
        f"{BASE_URL}/projects",
        "project",
        params={"ownerId": [owner_id]},
    )


def transform(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": require_non_empty(project.get("id"), "project id"),
            "name": project.get("name"),
            "ownerId": (project.get("owner") or {}).get("id"),
            "createdAt": project.get("createdAt"),
            "updatedAt": project.get("updatedAt"),
        }
        for project in projects
    ]


@timeit
def load_projects(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderProjectSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderProjectSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    owner_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    run_cleanup: bool = True,
) -> list[str]:
    """
    Sync the projects belonging to a single Render workspace.

    :param run_cleanup: Pass False to defer this resource's cleanup to a later,
        explicit `cleanup()` call - used when descendant resources (environments,
        services) are fetched through these project ids after this call returns, so
        that if one of those descendant fetches fails partway through, a stale
        project isn't already deleted out from under still-valid descendants (which
        would otherwise leave those descendants pointing at a project that no longer
        exists, until the descendant's own cleanup eventually catches up).
    :return: The synced project ids, so the caller can fetch their environments.
    """
    projects = get(session, owner_id)
    transformed = transform(projects)
    load_projects(neo4j_session, transformed, owner_id, update_tag)
    if run_cleanup:
        cleanup(neo4j_session, common_job_parameters)
    return [project["id"] for project in transformed]
