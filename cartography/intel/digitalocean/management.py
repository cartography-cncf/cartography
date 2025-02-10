import logging

import neo4j
from digitalocean import Manager

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    manager: Manager,
    digitalocean_update_tag: int,
    common_job_parameters: dict,
) -> dict:
    projects_resources = sync_projects(
        neo4j_session,
        manager,
        digitalocean_update_tag,
        common_job_parameters,
    )
    return projects_resources


@timeit
def sync_projects(
    neo4j_session: neo4j.Session,
    manager: Manager,
    digitalocean_update_tag: int,
    common_job_parameters: dict,
) -> dict:
    logger.info("Syncing Projects")
    account_id = common_job_parameters["DO_ACCOUNT_ID"]
    projects_res = get_projects(manager)
    projects_resources = get_projects_resources(projects_res)
    projects = transform_projects(projects_res, account_id)
    load_projects(neo4j_session, projects, digitalocean_update_tag)
    cleanup_projects(neo4j_session, common_job_parameters)

    return projects_resources


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
def transform_projects(project_res: list, account_id: str) -> list:
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
            "account_id": account_id,
        }
        result.append(project)
    return result


@timeit
def load_projects(
    neo4j_session: neo4j.Session,
    data: list,
    digitalocean_update_tag: int,
) -> None:
    query = """
        MERGE (a:DOAccount{id:$AccountId})
        ON CREATE SET a.firstseen = timestamp()
        SET a.lastupdated = $digitalocean_update_tag

        MERGE (p:DOProject{id:$ProjectId})
        ON CREATE SET p.firstseen = timestamp()
        SET p.account_id = $AccountId,
        p.name = $Name,
        p.owner_uuid = $OwnerUuid,
        p.description = $Description,
        p.environment = $Environment,
        p.is_default = $IsDefault,
        p.created_at = $CreatedAt,
        p.updated_at = $UpdatedAt,
        p.lastupdated = $digitalocean_update_tag
        WITH p, a

        MERGE (a)-[r:RESOURCE]->(p)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $digitalocean_update_tag
        """
    for project in data:
        neo4j_session.run(
            query,
            AccountId=project["account_id"],
            ProjectId=project["id"],
            Name=project["name"],
            OwnerUuid=project["owner_uuid"],
            Description=project["description"],
            Environment=project["environment"],
            IsDefault=project["is_default"],
            CreatedAt=project["created_at"],
            UpdatedAt=project["updated_at"],
            digitalocean_update_tag=digitalocean_update_tag,
        )
    return


@timeit
def cleanup_projects(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    """
    Delete out-of-date DigitalOcean projects and relationships
    :param neo4j_session: The Neo4j session
    :param common_job_parameters: dict of other job parameters to pass to Neo4j
    :return: Nothing
    """
    run_cleanup_job(
        "digitalocean_project_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )
    return
