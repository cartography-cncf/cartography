import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import neo4j
from pydo import Client

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.digitalocean.util.pagination import get_paginated_list
from cartography.models.digitalocean.droplet import DODropletSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: Client,
    account_id: str,
    projects_resources: dict,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    logger.info("Syncing Droplets")
    droplets_res = get_droplets(client)
    droplets_by_project = transform_droplets(
        droplets_res, account_id, projects_resources
    )
    load_droplets(neo4j_session, account_id, droplets_by_project, update_tag)
    cleanup(neo4j_session, list(droplets_by_project.keys()), common_job_parameters)


@timeit
def get_droplets(client: Client) -> list:
    return get_paginated_list(client.droplets.list, "droplets")


def get_ips(
    droplet: dict[str, Any],
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    # Get IPv4 addresses
    ipv4_networks = droplet.get("networks", {}).get("v4", [])
    public_ip = next(
        (n["ip_address"] for n in ipv4_networks if n.get("type") == "public"),
        None,
    )
    private_ip = next(
        (n["ip_address"] for n in ipv4_networks if n.get("type") == "private"),
        None,
    )
    # Get IPv6 address
    # No private for IPv6
    ipv6_networks = droplet.get("networks", {}).get("v6", [])
    ip_v6_address = next(
        (n["ip_address"] for n in ipv6_networks if n.get("type") == "public"),
        None,
    )

    return public_ip, private_ip, ip_v6_address


@timeit
def transform_droplets(
    droplets_res: list,
    account_id: str,
    projects_resources: dict,
) -> Dict[str, List[Dict[str, Any]]]:
    droplets_by_project: Dict[str, List[Dict[str, Any]]] = {}
    for d in droplets_res:
        project_id = str(_get_project_id_for_droplet(d.get("id"), projects_resources))
        if project_id not in droplets_by_project:
            droplets_by_project[project_id] = []

        ip_address, private_ip_address, ip_v6_address = get_ips(d)
        droplet = {
            "id": d.get("id"),
            "name": d.get("name"),
            "locked": d.get("locked"),
            "status": d.get("status"),
            "features": d.get("features"),
            "region": d.get("region", {}).get("slug"),
            "created_at": d.get("created_at"),
            "image": d.get("image", {}).get("slug"),
            "size": d.get("size_slug"),
            "kernel": d.get("kernel"),
            "tags": d.get("tags"),
            "volumes": d.get("volume_ids"),
            "vpc_uuid": d.get("vpc_uuid"),
            "ip_address": ip_address,
            "private_ip_address": private_ip_address,
            "ip_v6_address": ip_v6_address,
            "account_id": account_id,
            "project_id": _get_project_id_for_droplet(d.get("id"), projects_resources),
        }
        droplets_by_project[project_id].append(droplet)
    return droplets_by_project


@timeit
def _get_project_id_for_droplet(
    droplet_id: int,
    project_resources: dict,
) -> Optional[str]:
    droplet_resource_name = "do:droplet:" + str(droplet_id)
    for project_id, resource_data in project_resources.items():
        for resource in resource_data:
            if resource.get("urn") == droplet_resource_name:
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
