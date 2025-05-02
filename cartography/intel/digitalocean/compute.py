import logging
from typing import Optional

import neo4j
from digitalocean import Manager

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    manager: Manager,
    projects_resources: dict,
    digitalocean_update_tag: int,
    common_job_parameters: dict,
) -> None:
    sync_droplets(
        neo4j_session,
        manager,
        projects_resources,
        digitalocean_update_tag,
        common_job_parameters,
    )


@timeit
def sync_droplets(
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
    cleanup_droplets(neo4j_session, common_job_parameters)


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
    data: list,
    digitalocean_update_tag: int,
) -> None:
    query = """
        MERGE (p:DOProject{id:$ProjectId})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $digitalocean_update_tag

        MERGE (d:DODroplet{id:$DropletId})
        ON CREATE SET d.firstseen = timestamp()
        SET d.account_id = $AccountId,
        d.name = $Name,
        d.locked = $Locked,
        d.status = $Status,
        d.features = $Features,
        d.region = $RegionSlug,
        d.created_at = $CreatedAt,
        d.image = $ImageSlug,
        d.size = $SizeSlug,
        d.kernel = $Kernel,
        d.ip_address = $IpAddress,
        d.private_ip_address = $PrivateIpAddress,
        d.project_id = $ProjectId,
        d.ip_v6_address = $IpV6Address,
        d.tags = $Tags,
        d.volumes = $Volumes,
        d.vpc_uuid = $VpcUuid,
        d.lastupdated = $digitalocean_update_tag
        WITH d, p

        MERGE (p)-[r:RESOURCE]->(d)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $digitalocean_update_tag
        """
    for droplet in data:
        neo4j_session.run(
            query,
            AccountId=droplet["account_id"],
            DropletId=droplet["id"],
            Name=droplet["name"],
            Locked=droplet["locked"],
            Status=droplet["status"],
            Features=droplet["features"],
            RegionSlug=droplet["region"],
            CreatedAt=droplet["created_at"],
            ImageSlug=droplet["image"],
            SizeSlug=droplet["size"],
            IpAddress=droplet["ip_address"],
            PrivateIpAddress=droplet["private_ip_address"],
            ProjectId=droplet["project_id"],
            IpV6Address=droplet["ip_v6_address"],
            Kernel=droplet["kernel"],
            Tags=droplet["tags"],
            Volumes=droplet["volumes"],
            VpcUuid=droplet["vpc_uuid"],
            digitalocean_update_tag=digitalocean_update_tag,
        )
    return


@timeit
def cleanup_droplets(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    """
    Delete out-of-date DigitalOcean droplets and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    run_cleanup_job(
        "digitalocean_droplet_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )
    return
