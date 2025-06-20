import logging
from typing import Any
from typing import Dict
from typing import List

import neo4j
import scaleway
from scaleway.account.v3 import AccountV3ProjectAPI

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.scaleway.organization import ScalewayOrganizationSchema
from cartography.models.scaleway.project import ScalewayProjectSchema
from cartography.util import dict_date_to_datetime
from cartography.util import timeit

logger = logging.getLogger(__name__)
# Connect and read timeouts of 60 seconds each; see https://requests.readthedocs.io/en/master/user/advanced/#timeouts
_TIMEOUT = (60, 60)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    client: scaleway.Client,
    common_job_parameters: Dict[str, Any],
    org_id: str,
    update_tag: int,
) -> List[Dict]:
    projects = get(client, org_id)
    formatted_projects = transform_projects(projects)
    load_projects(neo4j_session, formatted_projects, org_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)
    return projects


@timeit
def get(
    client: scaleway.Client,
    org_id: str,
) -> List[Dict[str, Any]]:
    api = AccountV3ProjectAPI(client)
    return api.list_projects_all(organization_id=org_id)


def transform_projects(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    formatted_projects = []
    for project in projects:
        description = project.description if project.description != "" else None
        if description == "":
            description = None
        formatted_project = {
            "id": project.id,
            "name": project.name,
            "description": description,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
        }
        formatted_projects.append(formatted_project)
        print(project)
    return formatted_projects


@timeit
def load_projects(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        ScalewayOrganizationSchema(),
        [{"id": org_id}],
        lastupdated=update_tag,
    )
    logger.info("Loading %d Scaleway Projects into Neo4j.", len(data))
    load(
        neo4j_session,
        ScalewayProjectSchema(),
        data,
        lastupdated=update_tag,
        ORG_ID=org_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]
) -> None:
    GraphJob.from_node_schema(ScalewayProjectSchema(), common_job_parameters).run(
        neo4j_session
    )
