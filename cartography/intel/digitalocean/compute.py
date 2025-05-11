import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from digitalocean import Manager

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.digitalocean.droplet import DODropletSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    manager: Manager,
    account_id: str,
    projects_resources: dict,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info("Syncing Droplets")
    droplets_res = get_droplets(manager)
    droplets_by_project = transform_droplets(
        droplets_res, account_id, projects_resources
    )
    load_droplets(neo4j_session, account_id, droplets_by_project, update_tag)
    cleanup(neo4j_session, list(droplets_by_project.keys()), common_job_parameters)


@timeit
def get_droplets(manager: Manager) -> list:
    return manager.get_all_droplets()


@timeit
def transform_droplets(
    droplets_res: list,
    account_id: str,
    projects_resources: dict,
) -> Dict[str, List[Dict[str, Any]]]:
    droplets_by_project: Dict[str, List[Dict[str, Any]]] = {}
    for d in droplets_res:
        project_id = str(_get_project_id_for_droplet(d.id, projects_resources))
        if project_id not in droplets_by_project:
            droplets_by_project[project_id] = []
        droplet = {
            "id": d.id,
            "name": d.name,
            "locked": d.locked,
            "status": d.status,
            "features": d.features,
            "region": d.region["slug"],
            "created_at": d.created_at,
            "image": d.image["slug"],
            "size": d.size_slug,
            "kernel": d.kernel,
            "tags": d.tags,
            "volumes": d.volume_ids,
            "vpc_uuid": d.vpc_uuid,
            "ip_address": d.ip_address,
            "private_ip_address": d.private_ip_address,
            "ip_v6_address": d.ip_v6_address,
            "account_id": account_id,
            "project_id": _get_project_id_for_droplet(d.id, projects_resources),
        }
        droplets_by_project[project_id].append(droplet)
    return droplets_by_project


@timeit
def _get_project_id_for_droplet(
    droplet_id: int,
    project_resources: dict,
) -> Optional[str]:
    for project_id, resource_list in project_resources.items():
        droplet_resource_name = "do:droplet:" + str(droplet_id)
        if droplet_resource_name in resource_list:
            return project_id
    return None


@timeit
def load_droplets(
    neo4j_session: neo4j.Session,
    account_id: str,
    data: Dict[str, List[Dict[str, Any]]],
    update_tag: int,
) -> None:
    for project_id, droplets in data.items():
        load(
            neo4j_session,
            DODropletSchema(),
            droplets,
            lastupdated=update_tag,
            PROJECT_ID=str(project_id),
            ACCOUNT_ID=str(account_id),
        )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    projects_ids: List[str],
    common_job_parameters: Dict[str, Any],
) -> None:
    for project_id in projects_ids:
        parameters = common_job_parameters.copy()
        parameters["PROJECT_ID"] = str(project_id)
        GraphJob.from_node_schema(DODropletSchema(), parameters).run(
            neo4j_session,
        )
