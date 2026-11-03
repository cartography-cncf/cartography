import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.render.util import BASE_URL
from cartography.intel.render.util import list_paginated
from cartography.intel.render.util import require_non_empty
from cartography.models.render.environment import RenderEnvironmentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get(session: requests.Session, project_ids: list[str]) -> list[dict[str, Any]]:
    if not project_ids:
        return []
    return list_paginated(
        session,
        f"{BASE_URL}/environments",
        "environment",
        params={"projectId": project_ids},
    )


def transform(
    environments: list[dict[str, Any]],
    owner_id: str,
) -> list[dict[str, Any]]:
    return [
        {
            "id": require_non_empty(environment.get("id"), "environment id"),
            "name": environment.get("name"),
            "projectId": environment.get("projectId"),
            # Environments carry no owner field of their own; they are fetched scoped
            # to a project already known to belong to this workspace.
            "ownerId": owner_id,
            "protectedStatus": environment.get("protectedStatus"),
            "networkIsolationEnabled": environment.get("networkIsolationEnabled"),
        }
        for environment in environments
    ]


@timeit
def load_environments(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    owner_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        RenderEnvironmentSchema(),
        data,
        lastupdated=update_tag,
        OWNER_ID=owner_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(RenderEnvironmentSchema(), common_job_parameters).run(
        neo4j_session,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    owner_id: str,
    project_ids: list[str],
    update_tag: int,
    common_job_parameters: dict[str, Any],
    run_cleanup: bool = True,
) -> list[dict[str, Any]]:
    """
    Sync the environments belonging to a single Render workspace.

    :param run_cleanup: Pass False to defer this resource's cleanup to a later,
        explicit `cleanup()` call - used when descendant resources (services) are
        fetched through this call's results after it returns, so that a stale
        environment isn't already deleted out from under still-valid descendants -
        see projects.py's `sync()` docstring for the same rationale.
    :return: The raw (un-transformed) environment objects, so the caller can read their
        embedded `ipAllowList` without a second network call.
    """
    environments = get(session, project_ids)
    transformed = transform(environments, owner_id)
    load_environments(neo4j_session, transformed, owner_id, update_tag)
    if run_cleanup:
        cleanup(neo4j_session, common_job_parameters)
    return environments
