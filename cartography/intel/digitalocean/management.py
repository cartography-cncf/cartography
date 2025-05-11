import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from digitalocean import Manager

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.digitalocean.project import DOProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    manager: Manager,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> dict:
    logger.info("Syncing Projects")
    projects_res = get_projects(manager)
    projects = transform_projects(projects_res)
    load_projects(neo4j_session, projects, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)

    return get_projects_resources(projects_res)


@timeit
def get_projects(manager: Manager) -> list:
    return manager.get_all_projects()


@timeit
def get_projects_resources(projects_res: list) -> dict:
    result = {}
    for p in projects_res:
        resources = p.get_all_resources()
        result[p.id] = resources
    return result


@timeit
def transform_projects(project_res: list) -> list:
    result = list()
    for p in project_res:
        project = {
            "id": p.id,
            "name": p.name,
            "owner_uuid": p.owner_uuid,
            "description": p.description,
            "environment": p.environment,
            "is_default": p.is_default,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }
        result.append(project)
    return result


@timeit
def load_projects(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    account_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DOProjectSchema(),
        data,
        lastupdated=update_tag,
        ACCOUNT_ID=str(account_id),
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DOProjectSchema(), common_job_parameters).run(
        neo4j_session,
    )
