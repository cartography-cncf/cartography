import logging
from typing import Optional
from typing import Dict, Any, List

import neo4j
from digitalocean import Manager

from cartography.util import timeit
from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.digitalocean.droplet import DODropletSchema

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    manager: Manager,
    projects_resources: dict,
    digitalocean_update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info("Syncing Droplets")
    account_id = common_job_parameters["DO_ACCOUNT_ID"]
    droplets_res = get_droplets(manager)
    droplets = transform_droplets(droplets_res, account_id, projects_resources)
    load_droplets(neo4j_session, droplets, digitalocean_update_tag)
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get_droplets(manager: Manager) -> list:
    return manager.get_all_droplets()


@timeit
def transform_droplets(
    droplets_res: list,
    account_id: str,
    projects_resources: dict,
) -> list:
    droplets = list()
    for d in droplets_res:
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
        droplets.append(droplet)
    return droplets


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
    data: List[Dict[str, Any]],
    update_tag: int,
) -> None:
    load(neo4j_session, DODropletSchema(), data, lastupdated=update_tag)


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DODropletSchema(), common_job_parameters).run(
        neo4j_session,
    )
