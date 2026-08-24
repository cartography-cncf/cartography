import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
from pydo import Client

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.digitalocean.util.pagination import get_paginated_list
from cartography.models.digitalocean.project import DOProjectSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Client,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> dict:
    logger.info("Syncing Projects")
    projects_res = get_projects(client)
    projects = transform_projects(projects_res)
    load_projects(neo4j_session, projects, account_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)

    return get_projects_resources(client, projects_res)


@timeit
def get_projects(client: Client) -> list:
    return get_paginated_list(client.projects.list, "projects")


@timeit
def get_projects_resources(client: Client, projects_res: list) -> dict:
    result = {}
    for p in projects_res:
        id = p.get("id")
        resources = get_paginated_list(
            client.projects.list_resources, "resources", project_id=id
        )
        result[id] = resources
    return result


@timeit
def transform_projects(project_res: list) -> list:
    result = list()
    for p in project_res:
        project = {
            "id": p["id"],
            "name": p.get("name"),
            "owner_uuid": p.get("owner_uuid"),
            "description": p.get("description"),
            "environment": p.get("environment"),
            "is_default": p.get("is_default"),
            "created_at": p.get("created_at"),
            "updated_at": p.get("updated_at"),
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
